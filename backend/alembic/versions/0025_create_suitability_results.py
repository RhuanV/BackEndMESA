"""create mesa_a.suitability_results (MCDA ranking per case — Fase 5)

Persists the ranked candidate sites produced by the MCDA suitability computation
for a município (optionally scoped to a case), keyed by a config hash so
identical re-runs are cached. Links to a case are nullable so this works before
a case exists.

Revision ID: 0025
Revises: 0024
Create Date: 2026-07-15
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.suitability_results (
            id SERIAL PRIMARY KEY,
            case_id INTEGER REFERENCES mesa_a.projeto(id) ON DELETE CASCADE,
            codigo_ibge VARCHAR(7) NOT NULL,
            config_hash VARCHAR(64) NOT NULL,
            rank INTEGER NOT NULL,
            total_score NUMERIC(6, 2) NOT NULL,
            slope_score NUMERIC(6, 2),
            land_use_score NUMERIC(6, 2),
            transport_score NUMERIC(6, 2),
            cost_score NUMERIC(6, 2),
            geom GEOMETRY(POINT, 4674),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_suitability_results_key "
            "ON mesa_a.suitability_results (codigo_ibge, config_hash, rank);"
        )
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_suitability_results_geom "
            "ON mesa_a.suitability_results USING GIST (geom);"
        )
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS mesa_a.suitability_results;"))
