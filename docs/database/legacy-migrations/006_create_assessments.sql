-- Sprint 2 — Simplified MESA assessments table (GEO-26).
-- Covers the qualifying criteria from the 2021 Support Manual that the frontend
-- currently collects in AssessmentForm: slope, distance to urban centers,
-- presence of obstacles, estimated cost, and coordinates.

-- The complete MESA schema (Terrain, InformationPlan, MESACriterion, AHP, ...)
-- is Maria Antonia's responsibility and will come in a later sprint — here
-- we only keep enough for the end-to-end demo flow.

CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    site_name VARCHAR(100) NOT NULL,
    average_slope NUMERIC(5, 2) NOT NULL CHECK (average_slope >= 0 AND average_slope <= 100),
    urban_center_distance NUMERIC(7, 2) NOT NULL CHECK (urban_center_distance >= 0),
    has_obstacles BOOLEAN NOT NULL DEFAULT FALSE,
    obstacle_description TEXT,
    estimated_cost NUMERIC(15, 2) NOT NULL CHECK (estimated_cost >= 0),
    latitude NUMERIC(9, 6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9, 6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    geom GEOMETRY(POINT, 4674),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessments_geom ON assessments USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments (created_at DESC);
