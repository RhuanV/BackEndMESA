CREATE TABLE state_boundaries (
    id SERIAL PRIMARY KEY,
    ibge_code VARCHAR(10),
    state_name VARCHAR(100),
    state_abbr VARCHAR(2),
    geom GEOMETRY(MULTIPOLYGON, 4674) NOT NULL
);

CREATE INDEX idx_state_boundaries_geom
ON state_boundaries
USING GIST (geom);