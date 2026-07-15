"""Persistence for the raster catalog and MCDA suitability results (Fase 5)."""

from __future__ import annotations

from geoavia_backend.core.db import cursor


class RasterCatalogRepository:
    def get(self, dataset: str, codigo_ibge: str | None) -> dict | None:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT id, dataset, codigo_ibge, file_path, srid, resolution_m,
                       nodata, source_url, generated_at
                  FROM mesa_a.raster_catalog
                 WHERE dataset = %s
                   AND codigo_ibge IS NOT DISTINCT FROM %s;
                """,
                (dataset, codigo_ibge),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def upsert(
        self,
        dataset: str,
        codigo_ibge: str | None,
        file_path: str,
        resolution_m: float | None,
        nodata: float | None,
        source_url: str | None,
    ) -> None:
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO mesa_a.raster_catalog
                    (dataset, codigo_ibge, file_path, resolution_m, nodata, source_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (dataset, codigo_ibge) DO UPDATE SET
                    file_path = EXCLUDED.file_path,
                    resolution_m = EXCLUDED.resolution_m,
                    nodata = EXCLUDED.nodata,
                    source_url = EXCLUDED.source_url,
                    generated_at = NOW();
                """,
                (dataset, codigo_ibge, file_path, resolution_m, nodata, source_url),
            )


class SuitabilityResultsRepository:
    def replace_for(
        self, codigo_ibge: str, config_hash: str, case_id: int | None, rows: list[dict]
    ) -> None:
        """Replaces the ranked results for a (codigo_ibge, config_hash) key."""
        with cursor() as cur:
            cur.execute(
                """
                DELETE FROM mesa_a.suitability_results
                 WHERE codigo_ibge = %s AND config_hash = %s;
                """,
                (codigo_ibge, config_hash),
            )
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO mesa_a.suitability_results
                        (case_id, codigo_ibge, config_hash, rank, total_score,
                         slope_score, land_use_score, transport_score, cost_score, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4674));
                    """,
                    (
                        case_id,
                        codigo_ibge,
                        config_hash,
                        r["rank"],
                        r["total_score"],
                        r.get("slope_score"),
                        r.get("land_use_score"),
                        r.get("transport_score"),
                        r.get("cost_score"),
                        r["longitude"],
                        r["latitude"],
                    ),
                )

    def list_for(self, codigo_ibge: str, config_hash: str) -> list[dict]:
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT rank, total_score, slope_score, land_use_score,
                       transport_score, cost_score,
                       ST_X(geom) AS longitude, ST_Y(geom) AS latitude
                  FROM mesa_a.suitability_results
                 WHERE codigo_ibge = %s AND config_hash = %s
                 ORDER BY rank;
                """,
                (codigo_ibge, config_hash),
            )
            return [dict(r) for r in cur.fetchall()]
