"""Persistence for the layer metadata catalog (mesa_a.layer_catalog).

All queries are parameterized. The upsert keys on ``layer_key`` so re-running
the ingestion is idempotent (updates in place, never duplicates rows).
"""

from __future__ import annotations

from psycopg2.extras import execute_batch

from geoavia_backend.core.db import cursor

# Columns written by the ingestion, in a fixed order shared by the upsert.
_UPSERT_COLUMNS = [
    "layer_key",
    "tema",
    "plano_informacao",
    "fonte",
    "fonte_principal",
    "data_atualizacao_fonte",
    "periodicidade",
    "segregacao",
    "datum",
    "epsg",
    "formato",
    "geometria",
    "observacoes",
    "endereco",
    "grupo",
    "data_type",
    "backend_table",
    "available",
]

# Columns returned by the read endpoints (id + catalog fields + timestamps).
_SELECT_COLUMNS = "id, " + ", ".join(_UPSERT_COLUMNS) + ", created_at, updated_at"


class LayerCatalogRepository:
    def upsert_many(self, entries: list[dict]) -> None:
        """Inserts or updates catalog rows keyed on ``layer_key`` (idempotent)."""
        if not entries:
            return

        placeholders = ", ".join(["%s"] * len(_UPSERT_COLUMNS))
        updates = ", ".join(
            f"{col} = EXCLUDED.{col}" for col in _UPSERT_COLUMNS if col != "layer_key"
        )
        sql = f"""
            INSERT INTO mesa_a.layer_catalog ({", ".join(_UPSERT_COLUMNS)})
            VALUES ({placeholders})
            ON CONFLICT (layer_key) DO UPDATE SET
                {updates},
                updated_at = NOW();
        """
        rows = [tuple(entry.get(col) for col in _UPSERT_COLUMNS) for entry in entries]
        with cursor() as cur:
            execute_batch(cur, sql, rows)

    def list(self, tema: str | None = None, grupo: str | None = None) -> list[dict]:
        """Returns catalog rows, optionally filtered by tema/grupo (exact match)."""
        clauses: list[str] = []
        params: list[object] = []
        if tema:
            clauses.append("tema = %s")
            params.append(tema)
        if grupo:
            clauses.append("grupo = %s")
            params.append(grupo)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with cursor(dict_rows=True) as cur:
            cur.execute(
                f"""
                SELECT {_SELECT_COLUMNS}
                FROM mesa_a.layer_catalog
                {where}
                ORDER BY tema, plano_informacao, fonte;
                """,
                tuple(params),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_by_key(self, layer_key: str) -> dict | None:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                f"SELECT {_SELECT_COLUMNS} FROM mesa_a.layer_catalog WHERE layer_key = %s;",
                (layer_key,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
