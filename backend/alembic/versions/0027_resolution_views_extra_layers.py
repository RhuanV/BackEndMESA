"""multi-resolution views for the Fase 4 vetorial layers (map rendering)

Creates z1/z2/z3 materialized views for the generic mesa_a.vetor_* tables added
in 0026 so they are servable by the /layers endpoint and render on the map,
mirroring the pattern of migration 0013. The views expose `id` + a simplified
`geom` (generic geometry — these layers are polygonal).

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-16
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

# base_view_prefix -> source table (all in mesa_a).
_LAYERS = {
    "incra_quilombolas": "vetor_incra_quilombolas",
    "incra_assentamentos": "vetor_incra_assentamentos",
    "mma_florestas_publicas": "vetor_mma_florestas_publicas",
    "cprm_geodiversidade": "vetor_cprm_geodiversidade",
    "ibge_biomas": "vetor_ibge_biomas",
}
_TOLERANCES = {"z1": 0.05, "z2": 0.01, "z3": 0.002}


def upgrade() -> None:
    for prefix, table in _LAYERS.items():
        for zoom, tol in _TOLERANCES.items():
            view = f"{prefix}_{zoom}"
            op.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view};"))
            op.execute(
                text(f"""
                CREATE MATERIALIZED VIEW {view} AS
                SELECT id, ST_SimplifyPreserveTopology(geom, {tol}) AS geom
                FROM mesa_a.{table};
                """)
            )
            op.execute(text(f"CREATE INDEX idx_{view}_geom ON {view} USING GIST (geom);"))


def downgrade() -> None:
    for prefix in _LAYERS:
        for zoom in _TOLERANCES:
            op.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {prefix}_{zoom};"))
