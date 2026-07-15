from geoavia_backend.core.db import cursor


class UserRepository:
    def get_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT u.id, u.username, u.role, u.profile_id, p.name AS profile_name
                  FROM users u
                  LEFT JOIN permission_profiles p ON p.id = u.profile_id
                 ORDER BY u.id
                 LIMIT %s OFFSET %s;
                """,
                (limit, offset),
            )
            return cur.fetchall()

    def obtain_user_from_username(self, username: str) -> dict | None:
        """Returns the full user record by username, or None."""
        with cursor(dict_rows=True) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
            return cur.fetchone()

    def obtain_user_from_id(self, user_id: int) -> dict | None:
        with cursor(dict_rows=True) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
            return cur.fetchone()

    def create(self, username: str, hash_password: str, role: str) -> int:
        with cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, hash, role) VALUES (%s, %s, %s) RETURNING id;",
                (username, hash_password, role),
            )
            return cur.fetchone()[0]

    def update_password_hash(self, user_id: int, new_hash: str) -> bool:
        with cursor() as cur:
            cur.execute(
                "UPDATE users SET hash = %s WHERE id = %s;",
                (new_hash, user_id),
            )
            return cur.rowcount > 0

    def update_role(self, user_id: int, role: str) -> bool:
        with cursor() as cur:
            cur.execute("UPDATE users SET role = %s WHERE id = %s;", (role, user_id))
            return cur.rowcount > 0

    def update_profile(self, user_id: int, profile_id: int | None) -> bool:
        with cursor() as cur:
            cur.execute(
                "UPDATE users SET profile_id = %s WHERE id = %s;", (profile_id, user_id)
            )
            return cur.rowcount > 0

    def delete(self, user_id: int) -> bool:
        with cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            return cur.rowcount > 0
