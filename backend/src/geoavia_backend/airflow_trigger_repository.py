"""Persistence for the DAG manual trigger audit log (Sprint 4 HU-23)."""
from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor

from geoavia_backend.database import DATABASE_URL


class AirflowTriggerRepository:
    def __init__(self) -> None:
        self.conn_params = DATABASE_URL

    def insert_log(
        self,
        user_id: int | None,
        username: str,
        user_role: str,
        dag_id: str,
        dag_run_id: str | None,
        status: str,
        error_message: str | None = None,
    ) -> int:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dag_trigger_log
                        (user_id, username, user_role, dag_id, dag_run_id, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (user_id, username, user_role, dag_id, dag_run_id, status, error_message),
                )
                conn.commit()
                return cur.fetchone()[0]

    def list_recent(self, limit: int = 100) -> list[dict]:
        """Returns the most recent triggers, newest first."""
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, user_id, username, user_role, dag_id, dag_run_id,
                           status, error_message, triggered_at
                    FROM dag_trigger_log
                    ORDER BY triggered_at DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                return cur.fetchall()
