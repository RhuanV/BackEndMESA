-- Sprint 3 — Resolution tables (Task 4).
--
-- Materialized views with simplified geometry to reduce the weight of the vector
-- data when the frontend zooms out. The client sends the zoom level
-- (z1/z2/z3) and the backend routes to the appropriate view.
--
-- Tolerances (in degrees, SRID 4674 / SIRGAS 2000):
--   z1 = 0.05   (~5.5 km) — zoom out, Brazil view
--   z2 = 0.01   (~1.1 km) — medium zoom, state view
--   z3 = 0.002  (~220 m)  — zoom in, municipality view
--
-- Points (assessments) do not get resolution views: simplification does not
-- apply and the volume is small; serving directly from the base table is enough.
--
-- Refresh: manual for now via `REFRESH MATERIALIZED VIEW ...;`. The
-- automation via an Airflow DAG is Task 5 of Sprint 3.

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
-- municipality_boundaries (MULTIPOLYGON, ~5570 features — heavy)
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
