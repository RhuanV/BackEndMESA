"""/layers endpoint logic — validates the input and routes the zoom level to the
corresponding PostGIS materialized view.

When the base view is empty (Airflow DAGs have not run yet), the service falls
back to a user-uploaded shapefile configured via /layers/{name}/source.
"""
from __future__ import annotations

from geoavia_backend.core.geo_params import normalize_zoom, parse_bbox
from geoavia_backend.repositories.layers import LayersRepository

# Whitelist of layers with resolution views. `properties` must match the columns
# exposed by the *_z1/z2/z3 views (see migration 0013, which derives them from
# mesa_a.vetor_limites_* with PT-BR column names).
LAYER_REGISTRY: dict[str, dict] = {
    "state_boundaries": {
        "base_view_prefix": "state_boundaries",
        "properties": ["codigo_ibge", "nome_estado", "sigla_estado"],
    },
    "municipality_boundaries": {
        "base_view_prefix": "municipality_boundaries",
        "properties": ["codigo_ibge", "nome_municipio", "sigla_estado"],
    },
}


class LayersService:
    def __init__(self) -> None:
        self.repo = LayersRepository()

    def fetch(
        self,
        layer_name: str,
        zoom: str | None,
        bbox_raw: str | None,
    ) -> dict:
        if layer_name not in LAYER_REGISTRY:
            raise ValueError(f"Unknown layer: {layer_name}")

        zoom = normalize_zoom(zoom)

        bbox = parse_bbox(bbox_raw) if bbox_raw else None

        cfg = LAYER_REGISTRY[layer_name]
        view_name = f"{cfg['base_view_prefix']}_{zoom}"

        result = self.repo.fetch_geojson(view_name, cfg["properties"], bbox)

        # Fallback: if the Airflow-managed base table is empty, serve the
        # user-uploaded shapefile that the admin configured for this layer.
        if not result.get("features"):
            fallback_upload_id = self.repo.get_source(layer_name)
            if fallback_upload_id is not None:
                result = self.repo.fetch_geojson_from_upload(fallback_upload_id, bbox)

        return result

    def get_source(self, layer_name: str) -> dict:
        if layer_name not in LAYER_REGISTRY:
            raise ValueError(f"Unknown layer: {layer_name}")
        upload_id = self.repo.get_source(layer_name)
        return {"layer_name": layer_name, "upload_id": upload_id}

    def set_source(self, layer_name: str, upload_id: int | None) -> None:
        if layer_name not in LAYER_REGISTRY:
            raise ValueError(f"Unknown layer: {layer_name}")
        self.repo.set_source(layer_name, upload_id)
