"""SQL helpers for the spatial screening flow (Sprint 4 HU-29).

All queries build the input point with `ST_SetSRID(ST_MakePoint(long, lat), 4674)`
so SIRGAS 2000 is guaranteed regardless of client-side handling.

`table_name` must come from a whitelist — it is interpolated as a SQL identifier
(not bound as a parameter). The whitelist lives in screening_service.
"""
from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor

from geoavia_backend.database import DATABASE_URL


class ScreeningRepository:
    SRID = 4674  # SIRGAS 2000 — required by HU-29 acceptance criteria

    def __init__(self) -> None:
        self.conn_params = DATABASE_URL

    def _exec_scalar(self, query: str, params: tuple) -> bool:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return bool(next(iter(row.values()))) if row else False

    def is_table_populated(self, table_name: str) -> bool:
        """True iff `table_name` exists AND has at least one row.

        Treats a non-existent table as "not populated" so the screening flow
        can surface it via the missing-layers response instead of 500ing.
        """
        try:
            query = f"SELECT EXISTS(SELECT 1 FROM {table_name}) AS populated"
            return self._exec_scalar(query, ())
        except psycopg2.errors.UndefinedTable:
            return False

    def municipality_exists(self, ibge_code: str) -> bool:
        query = """
            SELECT EXISTS(
                SELECT 1 FROM municipality_boundaries WHERE ibge_code = %s
            ) AS exists
        """
        return self._exec_scalar(query, (ibge_code,))

    def is_point_within_municipality(
        self, latitude: float, longitude: float, ibge_code: str
    ) -> bool:
        """True iff the input point falls inside the municipality polygon."""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM municipality_boundaries
                WHERE ibge_code = %s
                  AND ST_Within(
                    ST_SetSRID(ST_MakePoint(%s, %s), %s),
                    geom
                  )
            ) AS within
        """
        return self._exec_scalar(query, (ibge_code, longitude, latitude, self.SRID))

    def does_point_intersect(
        self, latitude: float, longitude: float, table_name: str
    ) -> bool:
        """True iff the input point intersects any feature in the given table."""
        query = f"""
            SELECT EXISTS(
                SELECT 1 FROM {table_name}
                WHERE ST_Intersects(
                    geom,
                    ST_SetSRID(ST_MakePoint(%s, %s), %s)
                )
            ) AS intersects
        """
        return self._exec_scalar(query, (longitude, latitude, self.SRID))
