"""add width_m, height_m, angle_deg and convert geom to POLYGON

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-08

Adds the three parameters that define the rectangular airport-site footprint:
  width_m   — strip width in meters (default 45 m, ANAC minimum)
  height_m  — strip length in meters (default 1200 m)
  angle_deg — clockwise rotation from North in degrees (default 0)

The `geom` column is changed from GEOMETRY(POINT) to GEOMETRY(POLYGON).
Existing rows are converted using the new column defaults so the migration
is fully self-contained and requires no manual data entry.
"""

from __future__ import annotations

import math

from sqlalchemy import text

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

# Default site footprint (used for pre-existing seed records)
_DEFAULT_WIDTH_M = 45.0
_DEFAULT_HEIGHT_M = 1200.0
_DEFAULT_ANGLE_DEG = 0.0


def _wkt_rectangle(
    lon: float, lat: float, width_m: float, height_m: float, angle_deg: float
) -> str:
    """Return a WKT POLYGON for a rectangle defined by centroid + dimensions + angle."""
    lat_rad = math.radians(lat)
    dlon = (width_m / 2) / (111320.0 * math.cos(lat_rad))
    dlat = (height_m / 2) / 111320.0
    angle_rad = math.radians(-angle_deg)  # negate: clockwise-from-North → CCW math

    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

    def rotate(dx: float, dy: float) -> tuple[float, float]:
        return cos_a * dx - sin_a * dy, sin_a * dx + cos_a * dy

    corners_local = [(-dlon, -dlat), (dlon, -dlat), (dlon, dlat), (-dlon, dlat)]
    coords = [(lon + rotate(dx, dy)[0], lat + rotate(dx, dy)[1]) for dx, dy in corners_local]
    coords.append(coords[0])  # close ring
    pts = ", ".join(f"{x} {y}" for x, y in coords)
    return f"POLYGON(({pts}))"


def upgrade() -> None:
    # 1) Add new dimension columns with defaults
    op.execute(
        text("""
        ALTER TABLE assessments
        ADD COLUMN IF NOT EXISTS width_m   NUMERIC(8,2) NOT NULL DEFAULT 45.0,
        ADD COLUMN IF NOT EXISTS height_m  NUMERIC(8,2) NOT NULL DEFAULT 1200.0,
        ADD COLUMN IF NOT EXISTS angle_deg NUMERIC(5,2) NOT NULL DEFAULT 0.0;
    """)
    )

    # 2) Add a temporary POLYGON column alongside the existing POINT geom
    op.execute(
        text("""
        ALTER TABLE assessments
        ADD COLUMN IF NOT EXISTS geom_poly GEOMETRY(POLYGON, 4674);
    """)
    )

    # 3) Fetch existing rows and compute polygons in Python (Shapely not guaranteed
    #    inside the migration env, so we use pure-math WKT construction)
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, longitude, latitude, width_m, height_m, angle_deg FROM assessments")
    ).fetchall()

    for row in rows:
        wkt = _wkt_rectangle(
            float(row.longitude),
            float(row.latitude),
            float(row.width_m),
            float(row.height_m),
            float(row.angle_deg),
        )
        conn.execute(
            text(
                "UPDATE assessments SET geom_poly = ST_SetSRID(ST_GeomFromText(:wkt), 4674) WHERE id = :id"
            ),
            {"wkt": wkt, "id": row.id},
        )

    # 4) Drop old POINT geom index and column, rename geom_poly → geom
    op.execute(text("DROP INDEX IF EXISTS idx_assessments_geom;"))
    op.execute(text("ALTER TABLE assessments DROP COLUMN IF EXISTS geom;"))
    op.execute(text("ALTER TABLE assessments RENAME COLUMN geom_poly TO geom;"))
    op.execute(
        text("""
        CREATE INDEX idx_assessments_geom ON assessments USING GIST (geom);
    """)
    )


def downgrade() -> None:
    # Revert to POINT geometry (centroid of each polygon)
    op.execute(
        text("""
        ALTER TABLE assessments
        ADD COLUMN IF NOT EXISTS geom_point GEOMETRY(POINT, 4674);
    """)
    )
    op.execute(
        text("""
        UPDATE assessments SET geom_point = ST_Centroid(geom);
    """)
    )
    op.execute(text("DROP INDEX IF EXISTS idx_assessments_geom;"))
    op.execute(text("ALTER TABLE assessments DROP COLUMN IF EXISTS geom;"))
    op.execute(text("ALTER TABLE assessments RENAME COLUMN geom_point TO geom;"))
    op.execute(
        text("""
        CREATE INDEX idx_assessments_geom ON assessments USING GIST (geom);
    """)
    )
    op.execute(
        text("""
        ALTER TABLE assessments
        DROP COLUMN IF EXISTS width_m,
        DROP COLUMN IF EXISTS height_m,
        DROP COLUMN IF EXISTS angle_deg;
    """)
    )
