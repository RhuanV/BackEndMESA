"""Data access for admin-issued password recovery codes."""

from __future__ import annotations

from datetime import datetime

from geoavia_backend.core.db import cursor


class PasswordResetRepository:
    def create_code(
        self,
        user_id: int,
        code_hash: str,
        expires_at: datetime,
        created_by: int | None,
    ) -> int:
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO password_reset_codes
                    (user_id, code_hash, expires_at, created_by)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, code_hash, expires_at, created_by),
            )
            return cur.fetchone()[0]

    def invalidate_active_for_user(self, user_id: int) -> None:
        """Burns any still-active codes so a user has at most one live code."""
        with cursor() as cur:
            cur.execute(
                "UPDATE password_reset_codes SET used_at = now() "
                "WHERE user_id = %s AND used_at IS NULL;",
                (user_id,),
            )

    def get_active_for_user(self, user_id: int) -> list[dict]:
        """Returns the user's unused, non-expired codes (newest first)."""
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT id, code_hash, attempts, expires_at
                FROM password_reset_codes
                WHERE user_id = %s AND used_at IS NULL AND expires_at > now()
                ORDER BY created_at DESC;
                """,
                (user_id,),
            )
            return cur.fetchall()

    def mark_used(self, code_id: int) -> None:
        with cursor() as cur:
            cur.execute(
                "UPDATE password_reset_codes SET used_at = now() WHERE id = %s;",
                (code_id,),
            )

    def increment_attempts(self, code_id: int) -> int:
        with cursor() as cur:
            cur.execute(
                "UPDATE password_reset_codes SET attempts = attempts + 1 "
                "WHERE id = %s RETURNING attempts;",
                (code_id,),
            )
            return cur.fetchone()[0]
