"""seed IBGE state boundaries

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-10

Populates ``mesa_a.vetor_limites_estaduais`` from a committed, gzipped SQL seed
(derived from the IBGE BR_UF_2025 mesh) so a fresh clone shows the state
boundaries layer by default — no shapefile or Airflow run required. Idempotent:
skips if the table already has data. Municipalities are intentionally not seeded
here (too large to commit); load them via the Airflow ``load_municipality_boundaries``
DAG.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

# backend/alembic/versions/<this> -> parents[2] == backend (or /app in the image)
_SEED_PATH = Path(__file__).resolve().parents[2] / "seed" / "state_boundaries.sql.gz"

_STATE_VIEWS = (
    "state_boundaries_z1",
    "state_boundaries_z2",
    "state_boundaries_z3",
)


def upgrade() -> None:
    conn = op.get_bind()

    already = conn.execute(sa.text("SELECT count(*) FROM mesa_a.vetor_limites_estaduais")).scalar()
    if already and already > 0:
        return  # already populated (e.g. by Airflow) — leave it as is

    if not _SEED_PATH.exists():
        return  # no seed shipped — leave empty; boundaries can be loaded later

    sql = gzip.decompress(_SEED_PATH.read_bytes()).decode("utf-8")
    # The seed is a batch of parameter-less INSERTs; psycopg2 runs them in one go.
    conn.exec_driver_sql(sql)

    # The zoom views are materialized from the base table — refresh so the API
    # (which reads state_boundaries_zN) returns the freshly-seeded geometry.
    for view in _STATE_VIEWS:
        op.execute(f"REFRESH MATERIALIZED VIEW {view}")


def downgrade() -> None:
    op.execute("TRUNCATE TABLE mesa_a.vetor_limites_estaduais RESTART IDENTITY;")
    for view in _STATE_VIEWS:
        op.execute(f"REFRESH MATERIALIZED VIEW {view}")
