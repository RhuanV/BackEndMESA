"""Persistence for the manual DAG trigger audit log."""
from __future__ import annotations

from geoavia_backend.core.db import cursor


class AirflowTriggerRepository:
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
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO dag_trigger_log
                    (user_id, username, user_role, dag_id, dag_run_id, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, username, user_role, dag_id, dag_run_id, status, error_message),
            )
            return cur.fetchone()[0]

    def list_recent(self, limit: int = 100) -> list[dict]:
        """Returns the most recent triggers, newest first."""
        with cursor(dict_rows=True) as cur:
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
