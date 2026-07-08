"""Repository for MESA assessments (Sprint 2 simplified schema).

Sprint 5 addendum: geom column is now GEOMETRY(POLYGON, 4674); the polygon
WKT is computed by mesa_service._build_polygon() and passed in. ST_AsGeoJSON
is returned by get_all() so the service can pass it through to the frontend.
"""
import psycopg2
from psycopg2.extras import RealDictCursor

from geoavia_backend.database import DATABASE_URL


class AssessmentRepository:
    def __init__(self) -> None:
        self.conn_params = DATABASE_URL

    def insert(
        self,
        site_name: str,
        average_slope: float,
        urban_center_distance: float,
        has_obstacles: bool,
        obstacle_description: str | None,
        estimated_cost: float,
        latitude: float,
        longitude: float,
        width_m: float,
        height_m: float,
        angle_deg: float,
        polygon_wkt: str,
    ) -> dict:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO assessments (
                        site_name, average_slope, urban_center_distance,
                        has_obstacles, obstacle_description, estimated_cost,
                        latitude, longitude, width_m, height_m, angle_deg, geom
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_GeomFromText(%s), 4674)
                    )
                    RETURNING id, site_name, average_slope, urban_center_distance,
                              has_obstacles, obstacle_description, estimated_cost,
                              latitude, longitude, width_m, height_m, angle_deg,
                              ST_AsGeoJSON(geom) AS geometry_geojson,
                              created_at;
                    """,
                    (
                        site_name, average_slope, urban_center_distance,
                        has_obstacles, obstacle_description, estimated_cost,
                        latitude, longitude,
                        width_m, height_m, angle_deg, polygon_wkt,
                    ),
                )
                conn.commit()
                row = dict(cur.fetchone())
                row["geometry"] = row.pop("geometry_geojson", None)
                return row

    def get_all(self) -> list[dict]:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, site_name, average_slope, urban_center_distance,
                           has_obstacles, obstacle_description, estimated_cost,
                           latitude, longitude, width_m, height_m, angle_deg,
                           ST_AsGeoJSON(geom) AS geometry_geojson,
                           created_at
                    FROM assessments
                    ORDER BY created_at DESC;
                    """
                )
                rows = []
                for r in cur.fetchall():
                    d = dict(r)
                    d["geometry"] = d.pop("geometry_geojson", None)
                    rows.append(d)
                return rows
