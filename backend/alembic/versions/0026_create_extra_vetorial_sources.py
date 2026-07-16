"""create generic vetorial tables for the remaining BDG sources (Fase 4)

Adds tables for the data sources still missing from the BDG (INCRA quilombolas
and assentamentos, MMA florestas públicas, CPRM geodiversidade, IBGE biomas).

Each uses a generic shape — a JSONB ``properties`` column plus a generic
``geometry`` column — so a DAG can ingest any source's shapefile robustly
without hardcoding attribute names (which vary per source and only become known
against the real download). This keeps Fase 4 additive and low-risk.

Revision ID: 0026
Revises: 0025
Create Date: 2026-07-15
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

_TABLES = [
    "vetor_incra_quilombolas",
    "vetor_incra_assentamentos",
    "vetor_mma_florestas_publicas",
    "vetor_cprm_geodiversidade",
    "vetor_ibge_biomas",
]


def upgrade() -> None:
    for table in _TABLES:
        op.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS mesa_a.{table} (
                id SERIAL PRIMARY KEY,
                properties JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                geom GEOMETRY(Geometry, 4674),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """)
        )
        op.execute(
            text(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_geom "
                f"ON mesa_a.{table} USING GIST (geom);"
            )
        )


def downgrade() -> None:
    for table in _TABLES:
        op.execute(text(f"DROP TABLE IF EXISTS mesa_a.{table};"))
