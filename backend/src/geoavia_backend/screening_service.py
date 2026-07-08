"""Business logic for the spatial screening prototype (Sprint 4 HU-29 + HU-26).

HU-29 introduced a binary classification (viavel/restrito) based on point-in-polygon
checks. HU-26 layers a graduated protective-buffer zone on top: a point that
clears the hard restriction but falls within a layer-specific safety distance
is classified `intermediario` — usable with caveats, not outright rejected.

Buffer distances reflect typical ICAO/ANAC protective zones for airport siting:
no other airport closer than ~10 km, transmission corridors clear of new
construction by ~100 m, etc. They are tunable here, not in the DB.

Restrictive layer set is still a first cut — only infrastructure. Environmental
restriction tables (UCs, APPs, terras indígenas) join the list when their
migrations land.
"""
from __future__ import annotations

from geoavia_backend.screening_repository import ScreeningRepository

# Whitelisted restrictive layers. Tuples of (table_name, public_label).
# Public label is what the response surfaces in `reasons` — keep stable so the
# front can map to a human string / icon.
# Updated to point at the mesa_a schema after the team refactor (PRs #17/#18).
RESTRICTIVE_LAYERS: list[tuple[str, str]] = [
    ("mesa_a.vetor_osm_aeroportos", "airport"),
    ("mesa_a.vetor_gov_rodovias_federais", "federal_highway"),
    ("mesa_a.vetor_osm_rodovias_federais", "federal_highway_osm"),
    ("mesa_a.vetor_osm_rodovias_estaduais", "state_highway_osm"),
    ("mesa_a.vetor_gov_ferrovias", "railway"),
    ("mesa_a.vetor_osm_ferrovias", "railway_osm"),
    ("mesa_a.vetor_gov_hidrovias", "waterway"),
    ("mesa_a.vetor_osm_hidrovias", "waterway_osm"),
    ("mesa_a.vetor_gov_portos", "port"),
    ("mesa_a.vetor_osm_linhas_transmissao", "power_line"),
]

# Protective buffer per public label (meters). A point that does not intersect
# the layer geometry but falls within this distance triggers the intermediate
# classification.
BUFFER_DISTANCES_M: dict[str, float] = {
    "airport": 10_000.0,
    "federal_highway": 500.0,
    "federal_highway_osm": 500.0,
    "state_highway_osm": 300.0,
    "railway": 500.0,
    "railway_osm": 500.0,
    "waterway": 300.0,
    "waterway_osm": 300.0,
    "port": 2_000.0,
    "power_line": 100.0,
}

STATUS_VIAVEL = "viavel"
STATUS_INTERMEDIARIO = "intermediario"
STATUS_RESTRITO = "restrito"
REASON_OUTSIDE_MUNICIPALITY = "outside_target_municipality"

# Numeric codes returned alongside the status string so the front can map to
# severity colors without string parsing. 0 = blocked, 1 = ok, 2 = caveat.
STATUS_CODES = {
    STATUS_RESTRITO: 0,
    STATUS_VIAVEL: 1,
    STATUS_INTERMEDIARIO: 2,
}


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
        # 1. Validate base layers populated. Addresses the HU-29 acceptance
        #    "validar se as camadas já foram povoadas pelo Airflow".
        missing = self._check_layers_ready()
        if missing:
            raise LayersNotReadyError(missing)

        # 2. Validate target municipality exists.
        if not self.repo.municipality_exists(target_municipality_ibge_code):
            raise ValueError(
                f"Municipality ibge_code not found: {target_municipality_ibge_code}"
            )

        # 3. Containment in the target municipality. Outside → hard restriction.
        within = self.repo.is_point_within_municipality(
            latitude, longitude, target_municipality_ibge_code
        )

        restrictive_reasons: list[str] = []
        intermediate_reasons: list[dict] = []

        if not within:
            restrictive_reasons.append(REASON_OUTSIDE_MUNICIPALITY)

        # 4. For each restrictive layer: hard intersection wins; otherwise check
        #    the protective buffer and record it as an intermediate reason.
        for table_name, label in RESTRICTIVE_LAYERS:
            if self.repo.does_point_intersect(latitude, longitude, table_name):
                restrictive_reasons.append(label)
                continue

            distance_m = BUFFER_DISTANCES_M.get(label)
            if distance_m and self.repo.is_point_within_buffer(
                latitude, longitude, table_name, distance_m
            ):
                intermediate_reasons.append(
                    {"layer": label, "buffer_meters": distance_m}
                )

        if restrictive_reasons:
            status = STATUS_RESTRITO
        elif intermediate_reasons:
            status = STATUS_INTERMEDIARIO
        else:
            status = STATUS_VIAVEL

        return {
            "status": status,
            "code": STATUS_CODES[status],
            "reasons": restrictive_reasons,
            "intermediate_reasons": intermediate_reasons,
            "validation": {
                "srid": self.repo.SRID,
                "target_municipality_ibge_code": target_municipality_ibge_code,
                "layers_checked": [label for _, label in RESTRICTIVE_LAYERS],
                "buffers_applied_m": dict(BUFFER_DISTANCES_M),
            },
        }

    def _check_layers_ready(self) -> list[str]:
        """Returns names of required tables that are empty (or [] if all OK)."""
        required = ["mesa_a.vetor_limites_municipais"] + [t for t, _ in RESTRICTIVE_LAYERS]
        return [t for t in required if not self.repo.is_table_populated(t)]
