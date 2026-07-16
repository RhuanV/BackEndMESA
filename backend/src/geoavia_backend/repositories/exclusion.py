"""Geometries for the MCDA eliminatório (exclusion) mask.

Returns, as GeoJSON clipped to a município, the areas a candidate site must
avoid: the hard-restriction layers with their protective buffers (reusing the
screening whitelist/distances) plus the exclusion-group vetorial layers
(conservation units, indigenous/quilombola lands, public forests). The raster
service rasterizes the union of these into the exclusion mask.

All table names come from internal whitelists (never user input); each query is
guarded so a missing/empty table is simply skipped.
"""

from __future__ import annotations

import json

from psycopg2 import sql

from geoavia_backend.core.db import cursor
from geoavia_backend.services.screening import BUFFER_DISTANCES_M, RESTRICTIVE_LAYERS

# Exclusion-group polygon layers (no buffer): burned into the mask where they
# intersect the município. Skipped if the table does not exist / is empty.
_EXCLUSION_TABLES: list[str] = [
    "mesa_a.vetor_mma_florestas_publicas",
    "mesa_a.vetor_incra_quilombolas",
    "mesa_a.vetor_gov_uc",
    "mesa_a.vetor_gov_terra_indigena",
]


def _table_exists(cur, qualified: str) -> bool:
    cur.execute("SELECT to_regclass(%s) IS NOT NULL;", (qualified,))
    return bool(cur.fetchone()[0])


class ExclusionRepository:
    def municipality(self, codigo_ibge: str) -> dict | None:
        """Returns {geojson, bounds:[minx,miny,maxx,maxy]} for the município, or None."""
        with cursor(dict_rows=True) as cur:
            cur.execute(
                """
                SELECT ST_AsGeoJSON(geom) AS geojson,
                       ST_XMin(geom) AS minx, ST_YMin(geom) AS miny,
                       ST_XMax(geom) AS maxx, ST_YMax(geom) AS maxy
                  FROM mesa_a.vetor_limites_municipais
                 WHERE codigo_ibge = %s
                 LIMIT 1;
                """,
                (codigo_ibge,),
            )
            row = cur.fetchone()
            if not row or not row["geojson"]:
                return None
            return {
                "geojson": json.loads(row["geojson"]),
                "bounds": [row["minx"], row["miny"], row["maxx"], row["maxy"]],
            }

    def exclusion_geometries(self, codigo_ibge: str) -> list[dict]:
        """Returns GeoJSON geometries (clipped to the município) to exclude."""
        geoms: list[dict] = []
        with cursor() as cur:
            # Reference to the município geometry, reused by every sub-query.
            muni = sql.SQL(
                "(SELECT geom FROM mesa_a.vetor_limites_municipais WHERE codigo_ibge = %s LIMIT 1)"
            )

            # Exclusion-group polygons: intersection with the município.
            for table in _EXCLUSION_TABLES:
                if not _table_exists(cur, table):
                    continue
                query = sql.SQL("""
                    SELECT ST_AsGeoJSON(ST_Intersection(t.geom, m.geom))
                      FROM {tbl} t, LATERAL {muni} m
                     WHERE ST_Intersects(t.geom, m.geom)
                       AND NOT ST_IsEmpty(ST_Intersection(t.geom, m.geom));
                """).format(tbl=sql.SQL(table), muni=muni)
                cur.execute(query, (codigo_ibge,))
                geoms.extend(json.loads(r[0]) for r in cur.fetchall() if r[0])

            # Hard-restriction layers with their protective buffer (meters).
            for table, label in RESTRICTIVE_LAYERS:
                if not _table_exists(cur, table):
                    continue
                buffer_m = BUFFER_DISTANCES_M.get(label, 0.0)
                query = sql.SQL("""
                    SELECT ST_AsGeoJSON(
                        ST_Intersection(
                            ST_Buffer(t.geom::geography, %s)::geometry, m.geom
                        )
                    )
                    FROM {tbl} t, LATERAL {muni} m
                    WHERE ST_DWithin(t.geom::geography, m.geom::geography, %s);
                """).format(tbl=sql.SQL(table), muni=muni)
                cur.execute(query, (buffer_m, codigo_ibge, buffer_m))
                geoms.extend(json.loads(r[0]) for r in cur.fetchall() if r[0] and r[0] != "null")
        return geoms
