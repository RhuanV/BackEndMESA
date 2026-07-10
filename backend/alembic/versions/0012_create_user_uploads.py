"""create user_uploaded_layers and user_uploaded_features tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-08
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
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
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_user_uploaded_layers_uploaded_at
        ON mesa_a.user_uploaded_layers (uploaded_at DESC);
    """)
    )

    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.user_uploaded_features (
            id SERIAL PRIMARY KEY,
            upload_id INTEGER NOT NULL
                REFERENCES mesa_a.user_uploaded_layers(id) ON DELETE CASCADE,
            properties JSONB NOT NULL DEFAULT '{}'::jsonb,
            geom GEOMETRY(GEOMETRY, 4674) NOT NULL
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_user_uploaded_features_upload_id
        ON mesa_a.user_uploaded_features (upload_id);
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_user_uploaded_features_geom
        ON mesa_a.user_uploaded_features USING GIST (geom);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS mesa_a.user_uploaded_features;"))
    op.execute(text("DROP TABLE IF EXISTS mesa_a.user_uploaded_layers;"))
