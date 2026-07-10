"""add mesa_a.base_layer_sources for upload-based layer fallback

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-08

Allows a user-uploaded shapefile to be designated as the data source for a
static base layer (e.g. state_boundaries) when the Airflow-managed tables are
empty. The mapping is stored here and read by layers_service on every request.
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.base_layer_sources (
            layer_name VARCHAR(100) PRIMARY KEY,
            upload_id  INTEGER
                REFERENCES mesa_a.user_uploaded_layers(id) ON DELETE SET NULL
        );
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS mesa_a.base_layer_sources;"))
