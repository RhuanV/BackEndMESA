-- Sprint 5 HU-31 — Shapefile import by the user.
--
-- Two-table model:
--   user_uploaded_layers   : upload metadata (who, when, name, original SRID)
--   user_uploaded_features : individual features with geometry reprojected to 4674
--                            e atributos preservados em JSONB
--
-- ON DELETE SET NULL on user_id preserves the upload history even if the
-- is removed — reports/auditing remain readable.

CREATE TABLE IF NOT EXISTS mesa_a.user_uploaded_layers (
    id SERIAL PRIMARY KEY,
    layer_name VARCHAR(150) NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(50) NOT NULL,
    user_role VARCHAR(20) NOT NULL,
    original_filename VARCHAR(255),
    source_srid INTEGER,
    feature_count INTEGER NOT NULL DEFAULT 0,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_uploaded_layers_uploaded_at
    ON mesa_a.user_uploaded_layers (uploaded_at DESC);

CREATE TABLE IF NOT EXISTS mesa_a.user_uploaded_features (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER NOT NULL
        REFERENCES mesa_a.user_uploaded_layers(id) ON DELETE CASCADE,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    geom GEOMETRY(GEOMETRY, 4674) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_uploaded_features_upload_id
    ON mesa_a.user_uploaded_features (upload_id);

CREATE INDEX IF NOT EXISTS idx_user_uploaded_features_geom
    ON mesa_a.user_uploaded_features USING GIST (geom);
