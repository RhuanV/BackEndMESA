"""Persistence for backend processing jobs (MCDA analysis runs).

Complements the Airflow DAG-run history: while Airflow tracks the data-ingestion
pipeline, this table records the jobs the backend itself runs. Append-only, all
queries parameterized.
"""

from __future__ import annotations

from geoavia_backend.core.db import cursor


class ProcessingLogRepository:
    def insert(
        self,
        job: str,
        status: str,
        layer: str | None = None,
        duration_ms: int | None = None,
        detail: str | None = None,
    ) -> int:
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO processing_log (job, layer, status, duration_ms, detail)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (job, layer, status, duration_ms, detail),
            )
            return cur.fetchone()[0]

    def list_recent(self, limit: int = 100) -> list[dict]:
        """Returns the most recent processing entries, newest first."""
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT id, job, layer, status, duration_ms, detail, created_at
                FROM processing_log
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (limit,),
            )
            return cur.fetchall()
