import psycopg2
from psycopg2.extras import RealDictCursor

from backend.database import DATABASE_URL


class UsuarioRepository:
    def __init__(self) -> None:
        # Em produção, use variáveis de ambiente (.env)
        self.conn_params = DATABASE_URL

    def get_all(self) -> list[dict]:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username, role FROM usuarios;")
                return cur.fetchall()

    def create(self, username: str, hash_password: str, role: str) -> int:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (username, hash, role) VALUES (%s, %s, %s) RETURNING id;",
                    (username, hash_password, role)
                )
                conn.commit()
                return cur.fetchone()[0]

    def update_username(self, user_id: int, new_username: str) -> bool:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE usuarios SET username = %s WHERE id = %s;",
                    (new_username, user_id)
                )
                conn.commit()
                return cur.rowcount > 0

    def delete(self, user_id: int) -> bool:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM usuarios WHERE id = %s;", (user_id,))
                conn.commit()
                return cur.rowcount > 0