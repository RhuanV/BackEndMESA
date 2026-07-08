"""Business logic for the /layers endpoint — validates input and routes
zoom levels to the matching PostGIS materialized view (Sprint 3, Tarefa 4 / Sprint 4 HU-24).
"""
from __future__ import annotations

from geoavia_backend.layers_repository import LayersRepository

ALLOWED_ZOOMS = ("z1", "z2", "z3")
DEFAULT_ZOOM = "z2"

# Whitelist of layers that have resolution views. Each entry maps the public
# layer name to the base table and the properties to expose.
# When adding a new layer, also add the matching materialized views in
# backend/migrations/009_create_resolution_views.sql.
LAYER_REGISTRY: dict[str, dict] = {
    "state_boundaries": {
        "base_view_prefix": "state_boundaries",
        "properties": ["gid", "codigo_ibge", "nome_estado", "sigla_estado"],
    },
    "municipality_boundaries": {
        "base_view_prefix": "municipality_boundaries",
        "properties": ["gid", "codigo_ibge", "nome_municipio", "sigla_estado"],
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

        zoom = zoom or DEFAULT_ZOOM
        if zoom not in ALLOWED_ZOOMS:
            raise ValueError(f"Invalid zoom level: {zoom}. Use z1, z2 or z3.")

        bbox = self._parse_bbox(bbox_raw) if bbox_raw else None

        cfg = LAYER_REGISTRY[layer_name]
        view_name = f"{cfg['base_view_prefix']}_{zoom}"

        return self.repo.fetch_geojson(view_name, cfg["properties"], bbox)

    @staticmethod
    def _parse_bbox(raw: str) -> tuple[float, float, float, float]:
        """Parses 'west,south,east,north' into a 4-float tuple."""
        parts = raw.split(",")
        if len(parts) != 4:
            raise ValueError("bbox must have 4 comma-separated values: west,south,east,north")
        try:
            west, south, east, north = (float(p) for p in parts)
        except ValueError as exc:
            raise ValueError("bbox values must be valid numbers") from exc

        if west >= east or south >= north:
            raise ValueError("bbox must satisfy west < east and south < north")

        return (west, south, east, north)
