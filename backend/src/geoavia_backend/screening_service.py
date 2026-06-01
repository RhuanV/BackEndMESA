"""Business logic for the spatial screening prototype (Sprint 4 HU-29).

Classifies a point as `viavel` or `restrito` based on whether it falls inside
the target municipality and avoids intersection with restrictive layers.

Restrictive layer set is a first cut — only infrastructure (airports, highways,
railways, waterways, ports, power lines). Environmental/legal restriction
tables (UCs, APPs, terras indígenas) will join the list once their migrations
land.
"""
from __future__ import annotations

from geoavia_backend.screening_repository import ScreeningRepository

# Whitelisted restrictive layers. Tuples of (table_name, public_label).
# Public label is what the response surfaces in `reasons` — keep stable so the
# front can map to a human string / icon.
RESTRICTIVE_LAYERS: list[tuple[str, str]] = [
    ("osm_airports", "airport"),
    ("gov_federal_highways", "federal_highway"),
    ("osm_federal_highways", "federal_highway_osm"),
    ("osm_state_highways", "state_highway_osm"),
    ("gov_railways", "railway"),
    ("osm_railways", "railway_osm"),
    ("gov_waterways", "waterway"),
    ("osm_waterways", "waterway_osm"),
    ("gov_ports", "port"),
    ("osm_power_lines", "power_line"),
]

STATUS_VIAVEL = "viavel"
STATUS_RESTRITO = "restrito"
REASON_OUTSIDE_MUNICIPALITY = "outside_target_municipality"


class LayersNotReadyError(Exception):
    """Raised when a required base table is empty — screening cannot run."""

    def __init__(self, missing_layers: list[str]) -> None:
        self.missing_layers = missing_layers
        super().__init__(
            "Required layers are not yet populated by Airflow: "
            + ", ".join(missing_layers)
        )


class ScreeningService:
    def __init__(self) -> None:
        self.repo = ScreeningRepository()

    def screen(
        self,
        latitude: float,
        longitude: float,
        target_municipality_ibge_code: str,
    ) -> dict:
        # 1. Validate base layers populated. This addresses the HU acceptance
        #    "validar se as camadas já foram povoadas pelo Airflow".
        missing = self._check_layers_ready()
        if missing:
            raise LayersNotReadyError(missing)

        # 2. Validate target municipality exists.
        if not self.repo.municipality_exists(target_municipality_ibge_code):
            raise ValueError(
                f"Municipality ibge_code not found: {target_municipality_ibge_code}"
            )

        # 3. Check containment in the target municipality.
        within = self.repo.is_point_within_municipality(
            latitude, longitude, target_municipality_ibge_code
        )

        reasons: list[str] = []
        if not within:
            reasons.append(REASON_OUTSIDE_MUNICIPALITY)

        # 4. Check intersection with each restrictive layer. We run all checks
        #    even if `within` is False, so the response is fully informative.
        for table_name, label in RESTRICTIVE_LAYERS:
            if self.repo.does_point_intersect(latitude, longitude, table_name):
                reasons.append(label)

        status = STATUS_VIAVEL if not reasons else STATUS_RESTRITO

        return {
            "status": status,
            "code": 1 if status == STATUS_VIAVEL else 0,
            "reasons": reasons,
            "validation": {
                "srid": self.repo.SRID,
                "target_municipality_ibge_code": target_municipality_ibge_code,
                "layers_checked": [label for _, label in RESTRICTIVE_LAYERS],
            },
        }

    def _check_layers_ready(self) -> list[str]:
        """Returns names of required tables that are empty (or [] if all OK)."""
        required = ["municipality_boundaries"] + [t for t, _ in RESTRICTIVE_LAYERS]
        return [t for t in required if not self.repo.is_table_populated(t)]
