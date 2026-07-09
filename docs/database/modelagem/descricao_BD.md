## draft!
This document is a draft describing the beginning of the database construction.
Initially, the database is composed of one table per information layer. The relationships have not been discussed yet.
The methodology's business rules have not been implemented yet, and studying those rules may help define the relationships.

## Creating zoom tables:
Follow this model, based on the existing tables, to create three more zoom tables.
Their creation should happen when the database is created.


## Model for line and polygon tables
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


## Model for point tables
DROP MATERIALIZED VIEW IF EXISTS aeroportos_z1;
DROP MATERIALIZED VIEW IF EXISTS aeroportos_z2;
DROP MATERIALIZED VIEW IF EXISTS aeroportos_z3;

CREATE MATERIALIZED VIEW aeroportos_z1 AS
SELECT gid, nome, municipio, uf, codigo_iata, codigo_icao, geom
FROM vetor_aeroportos;

CREATE MATERIALIZED VIEW aeroportos_z2 AS
SELECT gid, nome, municipio, uf, codigo_iata, codigo_icao, geom
FROM vetor_aeroportos;

CREATE MATERIALIZED VIEW aeroportos_z3 AS
SELECT gid, nome, municipio, uf, codigo_iata, codigo_icao, geom
FROM vetor_aeroportos;

CREATE INDEX idx_aeroportos_z1_geom ON aeroportos_z1 USING GIST (geom);
CREATE INDEX idx_aeroportos_z2_geom ON aeroportos_z2 USING GIST (geom);
CREATE INDEX idx_aeroportos_z3_geom ON aeroportos_z3 USING GIST (geom);

Use this document as a prompt to generate the other tables once the database creation .sql is approved.

## Relationships between tables
The relationships have not been decided yet. An obvious relationship is State - Municipality, but the municipality table is already loaded with the federative unit...
We should think about relationships that help visualize the data, saving on server-side computation.
**Update**: Now structured with 3 layers: Raw (raw data from ETL ingestion, auditing, and tracking); Catalog (organization of the layers, standardizations); and Analysis (define criteria, scores, and constraints). The relationships can be better understood by looking at the conceptual model.
## Backend implementation
We need to create the backend requests to deliver the data to the frontend. The initial idea is visualization. Let's start with vector data only and expand later.
A visualization request should include a center point (where the user is looking) and a zoom level (z1, z2, z3, depending on the level of detail). The request should return the information layers within the requested rectangle at the selected resolution. The zoom calculation should be done by the frontend.

We should discuss whether the backend implementation sends all information layers or only the requested ones (within the area, of course). Testing is the best way to evaluate the best solution. We need to figure out how to send the data (JSON??) to the frontend; there is probably a ready-made library that does this.

