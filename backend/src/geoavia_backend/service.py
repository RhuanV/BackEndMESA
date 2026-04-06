from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from geoavia_backend.database import ALGORITHM, SECRET_KEY
from geoavia_backend.repository import UserRepository

ALLOWED_ROLES = {"analyst", "admin", "dev"}
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

    def list_users(self) -> list[dict]:
        # Future logic: filter active users or check permissions
        return self.repo.get_all()

    def register_user(self, username: str, password: str, role: str = "analyst") -> int:
        """Registers a user by generating a password hash before persisting it."""

        clean_username = username.strip()
        if not clean_username:
            raise ValueError("Username must not be empty")

        clean_password = password.strip()
        if not clean_password:
            raise ValueError("Password must not be empty")

        clean_role = role.strip().lower()
        if clean_role not in ALLOWED_ROLES:
            raise ValueError("Invalid role. Use: analyst, admin or dev")

        password_hash = self.security.get_password_hash(clean_password)
        return self.repo.create(clean_username, password_hash, clean_role)

    def change_username(self, user_id: int, new_username: str) -> bool:
        """Updates the username with basic input validation."""
        clean_username = new_username.strip()
        if not clean_username:
            raise ValueError("Username must not be empty")

        return self.repo.update_username(user_id, clean_username)

    def delete_user(self, user_id: int) -> bool:
        """Deletes a user by ID in the database."""
        return self.repo.delete(user_id)

    def authenticate_user(self, username: str, password: str) -> dict | None:
        """Validates credentials and returns the user data if correct."""
        user = self.repo.obtain_user_from_username(username.strip())
        if not user:
            return None

        if not self.security.verify_password(password, user["hash"]):
            return None

        return user