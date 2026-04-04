import psycopg2
from psycopg2.extras import RealDictCursor

class UsuarioRepository:
    def __init__(self):
        # Em produção, use variáveis de ambiente (.env)
        self.conn_params = "host=localhost dbname=usuarios_MESA user=postgres password=123"

    def get_all(self):
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username FROM usuarios;")
                return cur.fetchall()

    def create(self, username, hash_password):
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (username, hash) VALUES (%s, %s) RETURNING id;",
                    (username, hash_password)
                )
                conn.commit()
                return cur.fetchone()[0]