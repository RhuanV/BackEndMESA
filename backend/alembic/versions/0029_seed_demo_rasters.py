"""register the demo município rasters in raster_catalog (offline demo)

Registers the committed demo slope/land-use GeoTIFFs (backend/seed) in
``mesa_a.raster_catalog`` so the MCDA suitability, GeoTIFF export and map overlay
work on a fresh clone with no Airflow raster run (see docs/adr/0007). Idempotent
via the catalog's (dataset, codigo_ibge) upsert. Skipped if the files are absent.

Revision ID: 0029
Revises: 0028
Create Date: 2026-07-16
"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

_DEMO_IBGE = "9999999"
# backend/alembic/versions/<this> -> parents[2] == backend (or /app in the image)
_SEED_DIR = Path(__file__).resolve().parents[2] / "seed"
_RASTERS = (
    ("anadem_slope", 30.0, -9999.0, _SEED_DIR / f"demo_{_DEMO_IBGE}_slope.tif"),
    ("mapbiomas_landuse", 30.0, 0.0, _SEED_DIR / f"demo_{_DEMO_IBGE}_landuse.tif"),
)


def upgrade() -> None:
    conn = op.get_bind()
    for dataset, resolution_m, nodata, path in _RASTERS:
        if not path.exists():
            continue
        conn.execute(
            sa.text("""
                INSERT INTO mesa_a.raster_catalog
                    (dataset, codigo_ibge, file_path, resolution_m, nodata, source_url)
                VALUES (:dataset, :ibge, :path, :res, :nodata, :src)
                ON CONFLICT (dataset, codigo_ibge) DO UPDATE SET
                    file_path = EXCLUDED.file_path,
                    resolution_m = EXCLUDED.resolution_m,
                    nodata = EXCLUDED.nodata,
                    generated_at = NOW();
            """),
            {
                "dataset": dataset,
                "ibge": _DEMO_IBGE,
                "path": str(path),
                "res": resolution_m,
                "nodata": nodata,
                "src": "seed:make_demo_seed",
            },
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM mesa_a.raster_catalog WHERE codigo_ibge = :c "
            "AND dataset IN ('anadem_slope', 'mapbiomas_landuse')"
        ).bindparams(c=_DEMO_IBGE)
    )
