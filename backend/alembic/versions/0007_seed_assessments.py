"""seed example assessments

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-08
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

_SEED_SITES = (
    "Sítio Planície Norte",
    "Sítio Serra Leste",
    "Sítio Vale Central",
    "Sítio Planalto Sul",
    "Sítio Chapada Oeste",
)


def upgrade() -> None:
    op.execute(text("""
        INSERT INTO assessments (
            site_name, average_slope, urban_center_distance,
            has_obstacles, obstacle_description, estimated_cost,
            latitude, longitude, geom
        ) VALUES
            ('Sítio Planície Norte', 3.5, 55.0, false, NULL, 12000000.00,
             -15.7801, -47.9292,
             ST_SetSRID(ST_MakePoint(-47.9292, -15.7801), 4674)),
            ('Sítio Serra Leste',   12.0, 80.0, true,
             'Torres de alta tensão a 2 km', 28000000.00,
             -19.9167, -43.9345,
             ST_SetSRID(ST_MakePoint(-43.9345, -19.9167), 4674)),
            ('Sítio Vale Central',  6.2, 45.0, false, NULL, 18500000.00,
             -22.9068, -43.1729,
             ST_SetSRID(ST_MakePoint(-43.1729, -22.9068), 4674)),
            ('Sítio Planalto Sul',  8.8, 70.0, false, NULL, 22000000.00,
             -25.4284, -49.2733,
             ST_SetSRID(ST_MakePoint(-49.2733, -25.4284), 4674)),
            ('Sítio Chapada Oeste', 4.1, 60.0, true,
             'Área de proteção ambiental próxima', 15000000.00,
             -12.9714, -38.5014,
             ST_SetSRID(ST_MakePoint(-38.5014, -12.9714), 4674))
        ON CONFLICT DO NOTHING;
    """))


def downgrade() -> None:
    placeholders = ", ".join(f"'{s}'" for s in _SEED_SITES)
    op.execute(text(f"DELETE FROM assessments WHERE site_name IN ({placeholders});"))
