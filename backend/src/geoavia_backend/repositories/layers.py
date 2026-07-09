"""Read repository for the map layer resolution views.

Spatial filtering uses the GIST index (`geom && envelope`); the GeoJSON is
assembled in SQL via repositories.geojson to avoid (de)serializing geometries
in Python.
"""
from __future__ import annotations

from geoavia_backend.core.db import cursor
from geoavia_backend.repositories.geojson import fetch_feature_collection


class LayersRepository:
    # Hard cap on features per response — trades fidelity for transport size
    # when a zoomed-out bbox catches thousands of polygons.
    MAX_FEATURES = 5000

    def fetch_geojson(
        self,
        view_name: str,
        properties: list[str],
        bbox: tuple[float, float, float, float] | None,
    ) -> dict:
        """`view_name` and `properties` MUST come from a whitelist — they are
        interpolated as SQL identifiers, not bound as parameters.
        """
        props_sql = ", ".join(f"'{p}', sub.{p}" for p in properties)
        where_sql = "WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4674)" if bbox else ""
        inner_sql = f"""
            SELECT {", ".join(properties)}, geom
            FROM {view_name}
            {where_sql}
            LIMIT {self.MAX_FEATURES}
        """
        return fetch_feature_collection(
            geometry_sql="ST_AsGeoJSON(sub.geom)",
            properties_sql=f"json_build_object({props_sql})",
            inner_sql=inner_sql,
            params=bbox if bbox is not None else (),
        )

    def fetch_geojson_from_upload(
        self,
        upload_id: int,
        bbox: tuple[float, float, float, float] | None,
    ) -> dict:
        """Fallback source: serve a user-uploaded shapefile when the static
        base-layer view is empty. Properties come from the stored JSONB blob.
        """
        bbox_sql = "AND geom && ST_MakeEnvelope(%s, %s, %s, %s, 4674)" if bbox else ""
        inner_sql = f"""
            SELECT properties, geom
            FROM mesa_a.user_uploaded_features
            WHERE upload_id = %s {bbox_sql}
            LIMIT {self.MAX_FEATURES}
        """
        params = (upload_id, *bbox) if bbox else (upload_id,)
        return fetch_feature_collection(
            geometry_sql="ST_AsGeoJSON(sub.geom)",
            properties_sql="sub.properties",
            inner_sql=inner_sql,
            params=params,
        )

    def get_source(self, layer_name: str) -> int | None:
        """Returns the upload_id configured as the fallback source, or None."""
        with cursor() as cur:
            cur.execute(
                "SELECT upload_id FROM mesa_a.base_layer_sources WHERE layer_name = %s",
                (layer_name,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def set_source(self, layer_name: str, upload_id: int | None) -> None:
        """Upserts the fallback upload source for layer_name."""
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO mesa_a.base_layer_sources (layer_name, upload_id)
                VALUES (%s, %s)
                ON CONFLICT (layer_name)
                DO UPDATE SET upload_id = EXCLUDED.upload_id;
                """,
                (layer_name, upload_id),
            )
