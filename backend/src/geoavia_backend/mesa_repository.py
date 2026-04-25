"""Repository for MESA assessments (Sprint 2 simplified schema)."""
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
    ) -> dict:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO assessments (
                        site_name, average_slope, urban_center_distance,
                        has_obstacles, obstacle_description, estimated_cost,
                        latitude, longitude, geom
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4674)
                    )
                    RETURNING id, site_name, average_slope, urban_center_distance,
                              has_obstacles, obstacle_description, estimated_cost,
                              latitude, longitude, created_at;
                    """,
                    (
                        site_name, average_slope, urban_center_distance,
                        has_obstacles, obstacle_description, estimated_cost,
                        latitude, longitude, longitude, latitude,
                    ),
                )
                conn.commit()
                return cur.fetchone()

    def get_all(self) -> list[dict]:
        with psycopg2.connect(self.conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, site_name, average_slope, urban_center_distance,
                           has_obstacles, obstacle_description, estimated_cost,
                           latitude, longitude, created_at
                    FROM assessments
                    ORDER BY created_at DESC;
                    """
                )
                return cur.fetchall()
