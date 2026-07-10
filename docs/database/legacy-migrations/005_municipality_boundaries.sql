CREATE TABLE municipality_boundaries (
    ibge_code VARCHAR(10),
    municipality_name VARCHAR(150),
    state_abbr VARCHAR(2),
    geom GEOMETRY(MULTIPOLYGON, 4674)
);

CREATE INDEX idx_municipality_boundaries_geom
ON municipality_boundaries
USING GIST (geom);