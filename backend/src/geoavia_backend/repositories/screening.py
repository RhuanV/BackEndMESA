"""SQL helpers for the spatial screening flow.

All queries build the input point with
`ST_SetSRID(ST_MakePoint(long, lat), 4674)`, guaranteeing SIRGAS 2000.

`table_name` comes from a whitelist — it is interpolated as a SQL identifier
(not as a parameter). The whitelist lives in screening_service.
"""
from __future__ import annotations

import psycopg2

from geoavia_backend.core.db import cursor


class ScreeningRepository:
    SRID = 4674  # SIRGAS 2000

    def _exec_scalar(self, query: str, params: tuple) -> bool:
        with cursor(dict_rows=True) as cur:
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
                SELECT 1 FROM mesa_a.vetor_limites_municipais WHERE codigo_ibge = %s
            ) AS exists
        """
        return self._exec_scalar(query, (ibge_code,))

    def is_point_within_municipality(
        self, latitude: float, longitude: float, ibge_code: str
    ) -> bool:
        """True iff the input point falls inside the municipality polygon."""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM mesa_a.vetor_limites_municipais
                WHERE codigo_ibge = %s
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

    def is_point_within_buffer(
        self,
        latitude: float,
        longitude: float,
        table_name: str,
        distance_meters: float,
    ) -> bool:
        """True if the point is within `distance_meters` of any feature in the
        table — i.e. inside the layer's protective buffer (intermediate zone).

        Uses ST_DWithin with a geography cast so the distance is in meters
        regardless of the layer's stored SRID. Both sides of the comparison are
        cast — geography distance on geometry inputs returns degrees, which would
        silently give wrong answers.
        """
        query = f"""
            SELECT EXISTS(
                SELECT 1 FROM {table_name}
                WHERE ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), %s)::geography,
                    %s
                )
            ) AS within_buffer
        """
        return self._exec_scalar(
            query, (longitude, latitude, self.SRID, distance_meters)
        )
