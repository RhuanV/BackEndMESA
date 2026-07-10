"""create state_boundaries table

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-08
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS state_boundaries (
            id SERIAL PRIMARY KEY,
            ibge_code VARCHAR(10),
            state_name VARCHAR(100),
            state_abbr VARCHAR(2),
            geom GEOMETRY(MULTIPOLYGON, 4674) NOT NULL
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_state_boundaries_geom
        ON state_boundaries USING GIST (geom);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS state_boundaries;"))
