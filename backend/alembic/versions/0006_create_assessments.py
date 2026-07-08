"""create assessments table

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-08
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS assessments (
            id SERIAL PRIMARY KEY,
            site_name VARCHAR(100) NOT NULL,
            average_slope NUMERIC(5, 2) NOT NULL
                CHECK (average_slope >= 0 AND average_slope <= 100),
            urban_center_distance NUMERIC(7, 2) NOT NULL
                CHECK (urban_center_distance >= 0),
            has_obstacles BOOLEAN NOT NULL DEFAULT FALSE,
            obstacle_description TEXT,
            estimated_cost NUMERIC(15, 2) NOT NULL
                CHECK (estimated_cost >= 0),
            latitude NUMERIC(9, 6) NOT NULL
                CHECK (latitude BETWEEN -90 AND 90),
            longitude NUMERIC(9, 6) NOT NULL
                CHECK (longitude BETWEEN -180 AND 180),
            geom GEOMETRY(POINT, 4674),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """))
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_assessments_geom
        ON assessments USING GIST (geom);
    """))
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_assessments_created_at
        ON assessments (created_at DESC);
    """))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS assessments;"))
