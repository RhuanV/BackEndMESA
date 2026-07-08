-- Sprint 5 — Repointe das resolution views (Sprint 4 HU-24) pras tabelas
-- novas do schema mesa_a, que substituiram state_boundaries / municipality_boundaries
-- após o refator do time (PRs #17, #18).
--
-- Mantemos os nomes das views (state_boundaries_z*, municipality_boundaries_z*)
-- pra não quebrar layers_service / dag_refresh_resolution_views. Mudamos só
-- a fonte e os nomes de coluna.

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
