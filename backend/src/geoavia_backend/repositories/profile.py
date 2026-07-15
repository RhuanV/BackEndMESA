"""Persistence for custom permission profiles.

All queries are parameterized. Permissions are stored as a Postgres TEXT[]
column; psycopg2 adapts Python lists to/from arrays automatically.
"""

from __future__ import annotations

from geoavia_backend.core.db import cursor

_COLUMNS = "id, name, description, permissions, is_system, created_at, updated_at"


class ProfileRepository:
    def list(self) -> list[dict]:
        with cursor(dict_rows=True) as cur:
            cur.execute(f"SELECT {_COLUMNS} FROM permission_profiles ORDER BY name;")
            return [dict(row) for row in cur.fetchall()]

    def get_by_id(self, profile_id: int) -> dict | None:
        with cursor(dict_rows=True) as cur:
            cur.execute(f"SELECT {_COLUMNS} FROM permission_profiles WHERE id = %s;", (profile_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_permissions(self, profile_id: int) -> list[str]:
        """Returns just the permission list for a profile (or [] if missing)."""
        with cursor(dict_rows=True) as cur:
            cur.execute("SELECT permissions FROM permission_profiles WHERE id = %s;", (profile_id,))
            row = cur.fetchone()
            return list(row["permissions"]) if row and row["permissions"] else []

    def create(self, name: str, description: str | None, permissions: list[str]) -> int:
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO permission_profiles (name, description, permissions, is_system)
                VALUES (%s, %s, %s, FALSE)
                RETURNING id;
                """,
                (name, description, permissions),
            )
            return cur.fetchone()[0]

    def update(self, profile_id: int, description: str | None, permissions: list[str]) -> bool:
        with cursor() as cur:
            cur.execute(
                """
                UPDATE permission_profiles
                   SET description = %s, permissions = %s, updated_at = NOW()
                 WHERE id = %s;
                """,
                (description, permissions, profile_id),
            )
            return cur.rowcount > 0

    def delete(self, profile_id: int) -> bool:
        with cursor() as cur:
            cur.execute("DELETE FROM permission_profiles WHERE id = %s;", (profile_id,))
            return cur.rowcount > 0

    def name_exists(self, name: str) -> bool:
        with cursor(dict_rows=True) as cur:
            cur.execute("SELECT 1 FROM permission_profiles WHERE name = %s;", (name,))
            return cur.fetchone() is not None
