"""create mesa_a.raster_catalog + enable postgis_raster (Fase 5)

Registry of raster products (ANADEM MDT, derived slope, MapBiomas land use and
computed suitability) stored as Cloud-Optimized GeoTIFFs on the shared raster
volume. The postgis_raster extension is enabled for optional in-DB raster ops.

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-15
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_raster;"))
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS mesa_a.raster_catalog (
            id SERIAL PRIMARY KEY,
            dataset VARCHAR(40) NOT NULL
                CHECK (dataset IN ('anadem_mdt', 'anadem_slope',
                                   'mapbiomas_landuse', 'suitability')),
            codigo_ibge VARCHAR(7),
            file_path TEXT NOT NULL,
            srid INTEGER NOT NULL DEFAULT 4674,
            resolution_m NUMERIC(10, 3),
            nodata DOUBLE PRECISION,
            bbox GEOMETRY(POLYGON, 4674),
            checksum TEXT,
            source_url TEXT,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (dataset, codigo_ibge)
        );
    """)
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_raster_catalog_bbox "
            "ON mesa_a.raster_catalog USING GIST (bbox);"
        )
    )
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_raster_catalog_dataset "
            "ON mesa_a.raster_catalog (dataset, codigo_ibge);"
        )
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS mesa_a.raster_catalog;"))
