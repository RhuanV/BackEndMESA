"""create materialized views for multi-resolution rendering

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-08

z1 (0.05 deg ≈ 5.5 km) — Brasil
z2 (0.01 deg ≈ 1.1 km) — estado
z3 (0.002 deg ≈ 220 m) — município
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- state_boundaries ---
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z1;"))
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z2;"))
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z3;"))

    op.execute(text("""
        CREATE MATERIALIZED VIEW state_boundaries_z1 AS
        SELECT id, ibge_code, state_name, state_abbr,
               ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM state_boundaries;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW state_boundaries_z2 AS
        SELECT id, ibge_code, state_name, state_abbr,
               ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM state_boundaries;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW state_boundaries_z3 AS
        SELECT id, ibge_code, state_name, state_abbr,
               ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM state_boundaries;
    """))
    op.execute(text("""
        CREATE INDEX idx_state_boundaries_z1_geom ON state_boundaries_z1 USING GIST (geom);
    """))
    op.execute(text("""
        CREATE INDEX idx_state_boundaries_z2_geom ON state_boundaries_z2 USING GIST (geom);
    """))
    op.execute(text("""
        CREATE INDEX idx_state_boundaries_z3_geom ON state_boundaries_z3 USING GIST (geom);
    """))

    # --- municipality_boundaries ---
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z1;"))
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z2;"))
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z3;"))

    op.execute(text("""
        CREATE MATERIALIZED VIEW municipality_boundaries_z1 AS
        SELECT ibge_code, municipality_name, state_abbr,
               ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM municipality_boundaries;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW municipality_boundaries_z2 AS
        SELECT ibge_code, municipality_name, state_abbr,
               ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM municipality_boundaries;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW municipality_boundaries_z3 AS
        SELECT ibge_code, municipality_name, state_abbr,
               ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM municipality_boundaries;
    """))
    op.execute(text("""
        CREATE INDEX idx_municipality_boundaries_z1_geom
        ON municipality_boundaries_z1 USING GIST (geom);
    """))
    op.execute(text("""
        CREATE INDEX idx_municipality_boundaries_z2_geom
        ON municipality_boundaries_z2 USING GIST (geom);
    """))
    op.execute(text("""
        CREATE INDEX idx_municipality_boundaries_z3_geom
        ON municipality_boundaries_z3 USING GIST (geom);
    """))


def downgrade() -> None:
    for view in (
        "state_boundaries_z1", "state_boundaries_z2", "state_boundaries_z3",
        "municipality_boundaries_z1", "municipality_boundaries_z2", "municipality_boundaries_z3",
    ):
        op.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view};"))
