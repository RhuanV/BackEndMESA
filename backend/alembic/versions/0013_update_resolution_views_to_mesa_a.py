"""repoint resolution views to mesa_a schema tables

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-08

Replaces the views created in 0010 (which sourced from the legacy
state_boundaries / municipality_boundaries tables) with views that read from
mesa_a.vetor_limites_estaduais and mesa_a.vetor_limites_municipais.

The view NAMES are preserved so layers_service and dag_refresh_resolution_views
require no changes. Only the source tables and column names change.

NOTE: the mesa_a source tables are populated by Airflow DAGs. If they are empty
when this migration runs, the views will be created successfully but will return
zero rows until the DAGs load data.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

_STATE_VIEWS = (
    "state_boundaries_z1",
    "state_boundaries_z2",
    "state_boundaries_z3",
)
_MUNI_VIEWS = (
    "municipality_boundaries_z1",
    "municipality_boundaries_z2",
    "municipality_boundaries_z3",
)


def upgrade() -> None:
    for view in _STATE_VIEWS + _MUNI_VIEWS:
        op.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view};"))

    # State views — source: mesa_a.vetor_limites_estaduais
    op.execute(text("""
        CREATE MATERIALIZED VIEW state_boundaries_z1 AS
        SELECT gid, codigo_ibge, nome_estado, sigla_estado,
               ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM mesa_a.vetor_limites_estaduais;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW state_boundaries_z2 AS
        SELECT gid, codigo_ibge, nome_estado, sigla_estado,
               ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM mesa_a.vetor_limites_estaduais;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW state_boundaries_z3 AS
        SELECT gid, codigo_ibge, nome_estado, sigla_estado,
               ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM mesa_a.vetor_limites_estaduais;
    """))
    for view in _STATE_VIEWS:
        op.execute(text(
            f"CREATE INDEX idx_{view}_geom ON {view} USING GIST (geom);"
        ))

    # Municipality views — source: mesa_a.vetor_limites_municipais
    op.execute(text("""
        CREATE MATERIALIZED VIEW municipality_boundaries_z1 AS
        SELECT gid, codigo_ibge, nome_municipio, sigla_estado,
               ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM mesa_a.vetor_limites_municipais;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW municipality_boundaries_z2 AS
        SELECT gid, codigo_ibge, nome_municipio, sigla_estado,
               ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM mesa_a.vetor_limites_municipais;
    """))
    op.execute(text("""
        CREATE MATERIALIZED VIEW municipality_boundaries_z3 AS
        SELECT gid, codigo_ibge, nome_municipio, sigla_estado,
               ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
        FROM mesa_a.vetor_limites_municipais;
    """))
    for view in _MUNI_VIEWS:
        op.execute(text(
            f"CREATE INDEX idx_{view}_geom ON {view} USING GIST (geom);"
        ))


def downgrade() -> None:
    # Restore views from revision 0010 (legacy state_boundaries tables)
    for view in _STATE_VIEWS + _MUNI_VIEWS:
        op.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view};"))

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
    for view in _STATE_VIEWS + _MUNI_VIEWS:
        op.execute(text(
            f"CREATE INDEX idx_{view}_geom ON {view} USING GIST (geom);"
        ))
