"""Repository for MESA assessments.

geom is GEOMETRY(POLYGON, 4674); the polygon WKT comes from
mesa_service._build_polygon(). Rows expose ST_AsGeoJSON(geom) as `geometry`.
"""
from geoavia_backend.core.db import cursor


class AssessmentRepository:
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
        with cursor(dict_rows=True) as cur:
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
            row = dict(cur.fetchone())
            row["geometry"] = row.pop("geometry_geojson", None)
            return row

    def get_all(self) -> list[dict]:
        with cursor(dict_rows=True) as cur:
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
