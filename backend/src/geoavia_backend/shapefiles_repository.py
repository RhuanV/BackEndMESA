"""Persistence layer for user-uploaded shapefiles (Sprint 5 HU-31).

Stores metadata (one row per upload) and features (one row per geometry)
in the `mesa_a` schema, alongside the other vector layers managed by the
team.
"""
from __future__ import annotations

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

from geoavia_backend.database import DATABASE_URL
from geoavia_backend.geo_params import tolerance_for


class ShapefilesRepository:
    # Feature cap for the display endpoint. Higher than the static-layer cap
    # (5000) so a national base like BR_Municipios (~5570) is not truncated at
    # zoom-out; geometry is simplified per zoom, so the payload stays light.
    MAX_DISPLAY_FEATURES = 20_000

    def __init__(self) -> None:
        self.conn_params = DATABASE_URL

    def create_layer(
        self,
        layer_name: str,
        description: str | None,
        user_id: int | None,
        username: str,
        user_role: str,
        original_filename: str | None,
        source_srid: int | None,
    ) -> int:
        """Inserts the metadata row and returns the new layer id."""
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO mesa_a.user_uploaded_layers
                        (layer_name, description, user_id, username, user_role,
                         original_filename, source_srid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        layer_name,
                        description,
                        user_id,
                        username,
                        user_role,
                        original_filename,
                        source_srid,
                    ),
                )
                conn.commit()
                return cur.fetchone()[0]

    def insert_features(
        self,
        upload_id: int,
        features: list[tuple[str, str]],
    ) -> int:
        """Bulk-inserts features. Each tuple is (properties_json, geom_wkt_4674)."""
        if not features:
            return 0

        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                execute_batch(
                    cur,
                    """
                    INSERT INTO mesa_a.user_uploaded_features (upload_id, properties, geom)
                    VALUES (%s, %s::jsonb, ST_GeomFromText(%s, 4674));
                    """,
                    [(upload_id, props, wkt) for props, wkt in features],
                    page_size=200,
                )

                cur.execute(
                    """
                    UPDATE mesa_a.user_uploaded_layers
                    SET feature_count = (
                        SELECT COUNT(*) FROM mesa_a.user_uploaded_features
                        WHERE upload_id = %s
                    )
                    WHERE id = %s;
                    """,
                    (upload_id, upload_id),
                )
                conn.commit()
                return len(features)

    def list_layers(self, limit: int = 100) -> list[dict]:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, layer_name, description, user_id, username, user_role,
                           original_filename, source_srid, feature_count, uploaded_at
                    FROM mesa_a.user_uploaded_layers
                    ORDER BY uploaded_at DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                return cur.fetchall()

    def fetch_features_as_geojson(
        self,
        upload_id: int,
        zoom: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> dict:
        """Returns a GeoJSON FeatureCollection of the upload's features.

        Geometry is simplified on-the-fly per zoom level (same tolerances as
        the static resolution views) and, when a bbox is given, filtered to the
        viewport via the GIST index — keeping the payload small enough for the
        browser to render without blocking the main thread.
        """
        tolerance = tolerance_for(zoom)

        bbox_sql = "AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4674)" if bbox else ""

        query = f"""
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(
                            ST_SimplifyPreserveTopology(sub.geom, %s)
                        )::json,
                        'properties', sub.properties
                    )
                ), '[]'::json)
            ) AS geojson
            FROM (
                SELECT properties, geom
                FROM mesa_a.user_uploaded_features
                WHERE upload_id = %s {bbox_sql}
                LIMIT %s
            ) sub;
        """

        # psycopg2 binds %s positionally in order of appearance: tolerance
        # (outer ST_SimplifyPreserveTopology) → upload_id → bbox → limit.
        params = (tolerance, upload_id, *(bbox or ()), self.MAX_DISPLAY_FEATURES)

        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return (
                    row["geojson"]
                    if row
                    else {"type": "FeatureCollection", "features": []}
                )

    def layer_exists(self, upload_id: int) -> bool:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM mesa_a.user_uploaded_layers WHERE id = %s",
                    (upload_id,),
                )
                return cur.fetchone() is not None
