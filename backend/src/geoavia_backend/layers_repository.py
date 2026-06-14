"""Read-only repository for the resolution views used by the map layers endpoint."""
from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor

from geoavia_backend.database import DATABASE_URL


class LayersRepository:
    """Returns FeatureCollections from PostGIS resolution views.

    Spatial filter is applied via the GIST index (`geom && envelope`). The
    GeoJSON is assembled inside SQL (`json_build_object` + `ST_AsGeoJSON`) to
    avoid serializing/deserializing geometries in Python.
    """

    # Hard cap on features per response. Trades fidelity for transport size
    # when a zoomed-out bbox catches thousands of polygons.
    MAX_FEATURES = 5000

    def __init__(self) -> None:
        self.conn_params = DATABASE_URL

    def fetch_geojson(
        self,
        view_name: str,
        properties: list[str],
        bbox: tuple[float, float, float, float] | None,
    ) -> dict:
        """Returns a GeoJSON FeatureCollection from the given view.

        `view_name` and `properties` MUST come from a whitelist — they are
        interpolated as SQL identifiers, not bound as parameters.
        """
        props_sql = ", ".join(
            f"'{p}', sub.{p}" for p in properties
        )

        if bbox is not None:
            where_sql = "WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4674)"
            params: tuple = bbox
        else:
            where_sql = ""
            params = ()

        query = f"""
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(sub.geom)::json,
                        'properties', json_build_object({props_sql})
                    )
                ), '[]'::json)
            ) AS geojson
            FROM (
                SELECT {", ".join(properties)}, geom
                FROM {view_name}
                {where_sql}
                LIMIT {self.MAX_FEATURES}
            ) sub;
        """

        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return row["geojson"] if row else {"type": "FeatureCollection", "features": []}
