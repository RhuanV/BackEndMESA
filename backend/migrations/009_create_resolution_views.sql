-- Sprint 3 — Tabelas de resolução (Tarefa 4).
--
-- Materialized views com geometria simplificada para reduzir o peso dos dados
-- vetoriais quando o front pede zoom out. O cliente envia o nível de zoom
-- (z1/z2/z3) e o back roteia pra view adequada.
--
-- Tolerâncias (em graus, SRID 4674 / SIRGAS 2000):
--   z1 = 0.05   (~5.5 km) — zoom out, visão Brasil
--   z2 = 0.01   (~1.1 km) — zoom médio, visão estado
--   z3 = 0.002  (~220 m)  — zoom in, visão município
--
-- Pontos (assessments) não recebem views de resolução: simplificação não se
-- aplica e o volume é pequeno; servir direto da tabela base é suficiente.
--
-- Refresh: por enquanto manual via `REFRESH MATERIALIZED VIEW ...;`. A
-- automação via DAG do Airflow é a Tarefa 5 da Sprint 3.

-- ===========================================================================
-- state_boundaries (MULTIPOLYGON, 27 features)
-- ===========================================================================

DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z1;
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z2;
DROP MATERIALIZED VIEW IF EXISTS state_boundaries_z3;

CREATE MATERIALIZED VIEW state_boundaries_z1 AS
SELECT
    id,
    ibge_code,
    state_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
FROM state_boundaries;

CREATE MATERIALIZED VIEW state_boundaries_z2 AS
SELECT
    id,
    ibge_code,
    state_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
FROM state_boundaries;

CREATE MATERIALIZED VIEW state_boundaries_z3 AS
SELECT
    id,
    ibge_code,
    state_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
FROM state_boundaries;

CREATE INDEX idx_state_boundaries_z1_geom ON state_boundaries_z1 USING GIST (geom);
CREATE INDEX idx_state_boundaries_z2_geom ON state_boundaries_z2 USING GIST (geom);
CREATE INDEX idx_state_boundaries_z3_geom ON state_boundaries_z3 USING GIST (geom);

-- ===========================================================================
-- municipality_boundaries (MULTIPOLYGON, ~5570 features — peso alto)
-- ===========================================================================

DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z1;
DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z2;
DROP MATERIALIZED VIEW IF EXISTS municipality_boundaries_z3;

CREATE MATERIALIZED VIEW municipality_boundaries_z1 AS
SELECT
    ibge_code,
    municipality_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.05)::geometry(MULTIPOLYGON, 4674) AS geom
FROM municipality_boundaries;

CREATE MATERIALIZED VIEW municipality_boundaries_z2 AS
SELECT
    ibge_code,
    municipality_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.01)::geometry(MULTIPOLYGON, 4674) AS geom
FROM municipality_boundaries;

CREATE MATERIALIZED VIEW municipality_boundaries_z3 AS
SELECT
    ibge_code,
    municipality_name,
    state_abbr,
    ST_SimplifyPreserveTopology(geom, 0.002)::geometry(MULTIPOLYGON, 4674) AS geom
FROM municipality_boundaries;

CREATE INDEX idx_municipality_boundaries_z1_geom ON municipality_boundaries_z1 USING GIST (geom);
CREATE INDEX idx_municipality_boundaries_z2_geom ON municipality_boundaries_z2 USING GIST (geom);
CREATE INDEX idx_municipality_boundaries_z3_geom ON municipality_boundaries_z3 USING GIST (geom);
