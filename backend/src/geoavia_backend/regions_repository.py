"""SQL helpers for the /regions endpoints (Sprint 5 RF02).

Returns lightweight lookups (no geometry) for the estado/município hierarchy,
so the front can build dependent dropdowns without pulling full GeoJSON.
"""
from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor

from geoavia_backend.database import DATABASE_URL


class RegionsRepository:
    def __init__(self) -> None:
        self.conn_params = DATABASE_URL

    def list_states(self) -> list[dict]:
        """Returns one row per state (UF), sorted by name."""
        query = """
            SELECT codigo_ibge, sigla_estado, nome_estado
              FROM mesa_a.vetor_limites_estaduais
             WHERE sigla_estado IS NOT NULL
             ORDER BY nome_estado
        """
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]

    def list_municipalities_by_state(self, sigla_estado: str) -> list[dict]:
        """Returns the municipalities of a given UF, sorted by name.

        `sigla_estado` is the 2-letter UF code (e.g. 'SP'). Bound as a parameter
        — never interpolated.
        """
        query = """
            SELECT codigo_ibge, nome_municipio
              FROM mesa_a.vetor_limites_municipais
             WHERE sigla_estado = %s
               AND codigo_ibge IS NOT NULL
             ORDER BY nome_municipio
        """
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (sigla_estado.upper(),))
                return [dict(row) for row in cur.fetchall()]
