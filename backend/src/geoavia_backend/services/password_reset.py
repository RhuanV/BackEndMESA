"""Admin-issued, single-use password recovery codes.

Flow: an administrator issues a code for a user who forgot their password. The
code is random, hashed at rest, single-use and short-lived. It is relayed to
the user out-of-band; the user then resets their password on the login page by
providing username + code + new password. There is intentionally no email
integration.

Security properties:
  - Codes are hashed with the same context as passwords (never stored in clear).
  - Single-use and time-limited (RECOVERY_CODE_TTL_MINUTES).
  - Issuing a new code invalidates previous active codes for that user.
  - A code is burned after MAX_CODE_ATTEMPTS failed verifications.
  - Reset responses are generic (never reveal whether a username exists).
  - The protected DEV_USER cannot be targeted through this flow.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from geoavia_backend.core.database import DEV_USER
from geoavia_backend.core.passwords import validate_password_strength
from geoavia_backend.repositories.password_reset import PasswordResetRepository
from geoavia_backend.repositories.user import UserRepository
from geoavia_backend.services.user import SecurityService

RECOVERY_CODE_TTL_MINUTES = 30
MAX_CODE_ATTEMPTS = 5
CODE_LENGTH = 20
# Unambiguous alphabet (no O/0, I/1) so codes are easy to relay by voice/chat.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class PasswordRecoveryService:
    def __init__(
        self,
        users: UserRepository | None = None,
        codes: PasswordResetRepository | None = None,
        security: SecurityService | None = None,
    ) -> None:
        self.users = users or UserRepository()
        self.codes = codes or PasswordResetRepository()
        self.security = security or SecurityService()

    def issue_code(self, target_user_id: int, issued_by_id: int | None) -> dict:
        """Generates and stores a recovery code, returning the plaintext once."""
        user = self.users.obtain_user_from_id(target_user_id)
        if not user:
            raise ValueError("User not found")
        if user["username"] == DEV_USER:
            raise ValueError(
                "A recovery code cannot be issued for the protected developer user."
            )

        code = self._generate_code()
        code_hash = self.security.get_password_hash(code)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=RECOVERY_CODE_TTL_MINUTES
        )

        self.codes.invalidate_active_for_user(target_user_id)
        self.codes.create_code(target_user_id, code_hash, expires_at, issued_by_id)
        return {"code": code, "expires_at": expires_at.isoformat()}

    def reset_with_code(self, username: str, code: str, new_password: str) -> bool:
        """Resets the password if the code is valid. Raises a generic error
        otherwise (no information leak about usernames or codes)."""
        generic_error = ValueError("Invalid username or recovery code")

        clean_password = new_password.strip()
        # The policy error is about the password the caller just typed, so it is
        # safe to be specific here (it reveals nothing about accounts or codes).
        validate_password_strength(clean_password)

        user = self.users.obtain_user_from_username(username.strip())
        if not user or user["username"] == DEV_USER:
            raise generic_error

        clean_code = code.strip()
        for record in self.codes.get_active_for_user(user["id"]):
            if record["attempts"] >= MAX_CODE_ATTEMPTS:
                self.codes.mark_used(record["id"])  # burn exhausted code
                continue
            if self.security.verify_password(clean_code, record["code_hash"]):
                new_hash = self.security.get_password_hash(clean_password)
                self.users.update_password_hash(user["id"], new_hash)
                self.codes.mark_used(record["id"])
                return True
            self.codes.increment_attempts(record["id"])

        raise generic_error

    @staticmethod
    def _generate_code() -> str:
        return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(CODE_LENGTH))
