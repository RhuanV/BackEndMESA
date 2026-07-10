-- Sprint 5 — Repoint the resolution views (Sprint 4 HU-24) to the new
-- tables of the mesa_a schema, which replaced state_boundaries / municipality_boundaries
-- after the team's refactor (PRs #17, #18).
--
-- We keep the view names (state_boundaries_z*, municipality_boundaries_z*)
-- so as not to break layers_service / dag_refresh_resolution_views. We changed only
-- the source and column names.

DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z1;
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z2;
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z3;
DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z1;
DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z2;
DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z3;

CREATE MATERIALIZED VIEW state_boundaries_z1 AS
SELECT
    gid,
    codigo_ibge,
    nome_estado,
    sigla_estado,
    ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
FROM mesa_a.vetor_limites_estaduais;

CREATE MATERIALIZED VIEW state_boundaries_z2 AS
SELECT
    gid,
    codigo_ibge,
    nome_estado,
    sigla_estado,
    ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
FROM mesa_a.vetor_limites_estaduais;

CREATE MATERIALIZED VIEW state_boundaries_z3 AS
SELECT
    gid,
    codigo_ibge,
    nome_estado,
    sigla_estado,
    ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
FROM mesa_a.vetor_limites_estaduais;

CREATE INDEX idx_state_boundaries_z1_geom ON state_boundaries_z1 USING GIST (geom);
CREATE INDEX idx_state_boundaries_z2_geom ON state_boundaries_z2 USING GIST (geom);
CREATE INDEX idx_state_boundaries_z3_geom ON state_boundaries_z3 USING GIST (geom);

CREATE MATERIALIZED VIEW municipality_boundaries_z1 AS
SELECT
    gid,
    codigo_ibge,
    nome_municipio,
    sigla_estado,
    ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
FROM mesa_a.vetor_limites_municipais;

CREATE MATERIALIZED VIEW municipality_boundaries_z2 AS
SELECT
    gid,
    codigo_ibge,
    nome_municipio,
    sigla_estado,
    ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
FROM mesa_a.vetor_limites_municipais;

CREATE MATERIALIZED VIEW municipality_boundaries_z3 AS
SELECT
    gid,
    codigo_ibge,
    nome_municipio,
    sigla_estado,
    ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
FROM mesa_a.vetor_limites_municipais;

CREATE INDEX idx_municipality_boundaries_z1_geom ON municipality_boundaries_z1 USING GIST (geom);
CREATE INDEX idx_municipality_boundaries_z2_geom ON municipality_boundaries_z2 USING GIST (geom);
CREATE INDEX idx_municipality_boundaries_z3_geom ON municipality_boundaries_z3 USING GIST (geom);
