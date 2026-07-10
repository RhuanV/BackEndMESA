import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from geoavia_backend.core.database import ALGORITHM, SECRET_KEY, BOOTSTRAP_USER
from geoavia_backend.core.passwords import validate_password_strength
from geoavia_backend.core.roles import ROLES
from geoavia_backend.repositories.user import UserRepository

ACCESS_TOKEN_EXPIRE_MINUTES = 30


class SecurityService:
    """Centralizes the application's password hashing logic."""

    def __init__(self) -> None:
        # bcrypt_sha256 avoids the practical 72-byte limitation of pure bcrypt.
        # We keep bcrypt in the context to recognize legacy hashes, if they exist.
        self._pwd_context = CryptContext(
            schemes=["bcrypt_sha256", "bcrypt"],
            deprecated="auto",
        )

    def get_password_hash(self, password: str) -> str:
        """Generates the password hash for secure storage in the database."""
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Compares a plain-text password with the stored hash."""
        return self._pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, dados: dict) -> str:
        """Creates a JWT token with a 30-minute expiration."""
        if not SECRET_KEY:
            raise ValueError("SECRET_KEY not found in .env")

        payload = dados.copy()
        payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


class UserService:
    def __init__(self) -> None:
        self.repo = UserRepository()
        self.security = SecurityService()

    def list_users(self, limit: int = 100, offset: int = 0) -> list[dict]:
        users = self.repo.get_all(limit=limit, offset=offset)
        for u in users:
            u["is_protected"] = (u["username"] == BOOTSTRAP_USER)
        return users

    def register_user(self, username: str, password: str, role: str = "operador") -> int:
        """Registers a user by generating a password hash before persisting it."""

        clean_username = username.strip()
        if not clean_username:
            raise ValueError("Username must not be empty")

        clean_password = password.strip()
        if not clean_password:
            raise ValueError("Password must not be empty")
        validate_password_strength(clean_password)

        clean_role = role.strip().lower()
        if clean_role not in ROLES:
            raise ValueError("Invalid role. Use: operador, administrador or desenvolvedor")

        password_hash = self.security.get_password_hash(clean_password)
        return self.repo.create(clean_username, password_hash, clean_role)

    def create_pending_user(self, username: str, role: str = "operador") -> int:
        """Creates an account without a usable password (first-access flow).

        The account gets an unusable placeholder hash (a random secret nobody
        knows), so it cannot be logged into until the user sets a real password
        through the admin-issued recovery code. The admin never sets/knows it.
        """
        clean_username = username.strip()
        if not clean_username:
            raise ValueError("Username must not be empty")

        clean_role = role.strip().lower()
        if clean_role not in ROLES:
            raise ValueError("Invalid role. Use: operador, administrador or desenvolvedor")

        if self.repo.obtain_user_from_username(clean_username) is not None:
            raise ValueError("Username already exists")

        placeholder_hash = self.security.get_password_hash(secrets.token_urlsafe(32))
        return self.repo.create(clean_username, placeholder_hash, clean_role)

    def delete_user(self, user_id: int) -> bool:
        """Deletes a user by ID in the database."""
        # Protect root 'admin' user
        user = self.repo.obtain_user_from_id(user_id)
        if user and user["username"] == BOOTSTRAP_USER:
            raise ValueError(f"The protected bootstrap user ('{BOOTSTRAP_USER}') cannot be deleted.")
        return self.repo.delete(user_id)

    def change_password(self, user_id: int, new_password: str) -> bool:
        """Updates the password for a user after generating a secure hash."""
        clean_password = new_password.strip()
        if not clean_password:
            raise ValueError("Password must not be empty")
        validate_password_strength(clean_password)

        # Verify that the user exists and is not the root bootstrap user
        user = self.repo.obtain_user_from_id(user_id)
        if not user:
            return False
        if user["username"] == BOOTSTRAP_USER:
            raise ValueError(f"The password of the protected bootstrap user ('{BOOTSTRAP_USER}') cannot be changed through this route.")

        password_hash = self.security.get_password_hash(clean_password)
        return self.repo.update_password_hash(user_id, password_hash)

    def authenticate_user(self, username: str, password: str) -> dict | None:
        """Validates credentials and returns the user data if correct."""
        user = self.repo.obtain_user_from_username(username.strip())
        if not user:
            return None

        if not self.security.verify_password(password, user["hash"]):
            return None

        return user