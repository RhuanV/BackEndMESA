"""seed the demo município + Fase 4 vector layers (offline demo fixture)

Loads a small, synthetic demo município and its five vector layers from a
committed gzipped SQL seed so a fresh clone renders the Fase 4 layers on the map
with no Airflow run (see docs/adr/0007). The seed statements are self-guarded
(WHERE NOT EXISTS), so this migration is idempotent. Refreshes the affected
resolution views afterwards.

Revision ID: 0028
Revises: 0027
Create Date: 2026-07-16
"""

from __future__ import annotations

import gzip
from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

_DEMO_IBGE = "9999999"
# backend/alembic/versions/<this> -> parents[2] == backend (or /app in the image)
_SEED_PATH = Path(__file__).resolve().parents[2] / "seed" / f"demo_{_DEMO_IBGE}_vetor.sql.gz"

_VIEWS = (
    "municipality_boundaries_z1",
    "municipality_boundaries_z2",
    "municipality_boundaries_z3",
    "incra_quilombolas_z1", "incra_quilombolas_z2", "incra_quilombolas_z3",
    "incra_assentamentos_z1", "incra_assentamentos_z2", "incra_assentamentos_z3",
    "mma_florestas_publicas_z1", "mma_florestas_publicas_z2", "mma_florestas_publicas_z3",
    "cprm_geodiversidade_z1", "cprm_geodiversidade_z2", "cprm_geodiversidade_z3",
    "ibge_biomas_z1", "ibge_biomas_z2", "ibge_biomas_z3",
)


def upgrade() -> None:
    if not _SEED_PATH.exists():
        return  # no seed shipped — leave empty; layers load via Airflow later
    conn = op.get_bind()
    sql = gzip.decompress(_SEED_PATH.read_bytes()).decode("utf-8")
    conn.exec_driver_sql(sql)  # self-guarded INSERTs (idempotent)
    for view in _VIEWS:
        op.execute(f"REFRESH MATERIALIZED VIEW {view}")


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM mesa_a.vetor_limites_municipais WHERE codigo_ibge = :c"
        ).bindparams(c=_DEMO_IBGE)
    )
    for table in (
        "vetor_ibge_biomas",
        "vetor_incra_quilombolas",
        "vetor_incra_assentamentos",
        "vetor_mma_florestas_publicas",
        "vetor_cprm_geodiversidade",
    ):
        op.execute(f"DELETE FROM mesa_a.{table} WHERE properties->>'seed' = 'demo';")
    for view in _VIEWS:
        op.execute(f"REFRESH MATERIALIZED VIEW {view}")
