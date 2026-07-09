"""Persistence for user-uploaded shapefiles.

Stores metadata (one row per upload) and features (one row per geometry)
in the `mesa_a` schema, alongside the other vector layers.
"""
from __future__ import annotations

from psycopg2.extras import execute_batch

from geoavia_backend.core.db import cursor
from geoavia_backend.core.geo_params import tolerance_for
from geoavia_backend.repositories.geojson import fetch_feature_collection


class ShapefilesRepository:
    # Feature cap for the display endpoint. Higher than the static-layer cap
    # (5000) so a national base like BR_Municipios (~5570) is not truncated at
    # zoom-out; geometry is simplified per zoom, so the payload stays light.
    MAX_DISPLAY_FEATURES = 20_000

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
        with cursor() as cur:
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
            return cur.fetchone()[0]

    def insert_features(
        self,
        upload_id: int,
        features: list[tuple[str, str]],
    ) -> int:
        """Bulk-inserts features. Each tuple is (properties_json, geom_wkt_4674)."""
        if not features:
            return 0

        with cursor() as cur:
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
            return len(features)

    def list_layers(self, limit: int = 100) -> list[dict]:
        with cursor(dict_rows=True) as cur:
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
        """GeoJSON of the upload's features, simplified per zoom and optionally
        clipped to `bbox` (GIST index) so the payload stays browser-renderable.
        """
        tolerance = tolerance_for(zoom)
        bbox_sql = "AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4674)" if bbox else ""
        inner_sql = f"""
            SELECT properties, geom
            FROM mesa_a.user_uploaded_features
            WHERE upload_id = %s {bbox_sql}
            LIMIT %s
        """
        # Placeholders bind in text order: tolerance (geometry expr) → upload_id
        # → bbox → limit.
        params = (tolerance, upload_id, *(bbox or ()), self.MAX_DISPLAY_FEATURES)
        return fetch_feature_collection(
            geometry_sql="ST_AsGeoJSON(ST_SimplifyPreserveTopology(sub.geom, %s))",
            properties_sql="sub.properties",
            inner_sql=inner_sql,
            params=params,
        )

    def layer_exists(self, upload_id: int) -> bool:
        with cursor() as cur:
            cur.execute(
                "SELECT 1 FROM mesa_a.user_uploaded_layers WHERE id = %s",
                (upload_id,),
            )
            return cur.fetchone() is not None
