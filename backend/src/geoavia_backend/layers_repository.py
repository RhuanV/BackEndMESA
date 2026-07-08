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

    def fetch_geojson_from_upload(
        self,
        upload_id: int,
        bbox: tuple[float, float, float, float] | None,
    ) -> dict:
        """Returns a GeoJSON FeatureCollection from a user-uploaded shapefile.

        Used as a fallback when the static base-layer view is empty (Airflow
        tables not yet populated). Properties come from the stored JSONB blob.
        """
        if bbox is not None:
            where_sql = "AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4674)"
            params: tuple = (upload_id, *bbox)
        else:
            where_sql = ""
            params = (upload_id,)

        query = f"""
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(sub.geom)::json,
                        'properties', sub.properties
                    )
                ), '[]'::json)
            ) AS geojson
            FROM (
                SELECT properties, geom
                FROM mesa_a.user_uploaded_features
                WHERE upload_id = %s {where_sql}
                LIMIT {self.MAX_FEATURES}
            ) sub;
        """

        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return row["geojson"] if row else {"type": "FeatureCollection", "features": []}

    def get_source(self, layer_name: str) -> int | None:
        """Returns the upload_id configured as the fallback source for layer_name, or None."""
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT upload_id FROM mesa_a.base_layer_sources WHERE layer_name = %s",
                    (layer_name,),
                )
                row = cur.fetchone()
                return row[0] if row else None

    def set_source(self, layer_name: str, upload_id: int | None) -> None:
        """Upserts the fallback upload source for layer_name."""
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mesa_a.base_layer_sources (layer_name, upload_id)
                    VALUES (%s, %s)
                    ON CONFLICT (layer_name)
                    DO UPDATE SET upload_id = EXCLUDED.upload_id;
                    """,
                    (layer_name, upload_id),
                )
                conn.commit()
