"""create municipality_boundaries table

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-08
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS municipality_boundaries (
            ibge_code VARCHAR(10),
            municipality_name VARCHAR(150),
            state_abbr VARCHAR(2),
            geom GEOMETRY(MULTIPOLYGON, 4674)
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_municipality_boundaries_geom
        ON municipality_boundaries USING GIST (geom);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS municipality_boundaries;"))
