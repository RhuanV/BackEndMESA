"""SQL helpers for the /regions endpoints.

Returns lightweight lookups (no geometry) of the state/municipality hierarchy,
so the frontend can build dependent dropdowns without pulling full GeoJSON.
"""
from __future__ import annotations

from geoavia_backend.core.db import cursor


class RegionsRepository:
    def list_states(self) -> list[dict]:
        query = """
            SELECT codigo_ibge, sigla_estado, nome_estado
              FROM mesa_a.vetor_limites_estaduais
             WHERE sigla_estado IS NOT NULL
             ORDER BY nome_estado
        """
        with cursor(dict_rows=True) as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]

    def list_municipalities_by_state(self, sigla_estado: str) -> list[dict]:
        """`sigla_estado` (2-letter UF) is bound as a parameter, never interpolated."""
        query = """
            SELECT codigo_ibge, nome_municipio
              FROM mesa_a.vetor_limites_municipais
             WHERE sigla_estado = %s
               AND codigo_ibge IS NOT NULL
             ORDER BY nome_municipio
        """
        with cursor(dict_rows=True) as cur:
            cur.execute(query, (sigla_estado.upper(),))
            return [dict(row) for row in cur.fetchall()]
