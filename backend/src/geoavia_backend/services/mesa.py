"""MESA assessment and analysis service.

The analysis runs as a job with a deterministic score. Each site is stored as a
POLYGON built by _build_polygon() from the centroid and width/height/angle.
"""

from __future__ import annotations

import io
import json
import math
import os
import tempfile
import time
import uuid
import zipfile
from threading import Lock

import geopandas as gpd
from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, shape

from geoavia_backend.repositories.mesa import AssessmentRepository


def _to_float(value) -> float:
    return float(value) if value is not None else 0.0


def _build_polygon(
    lon: float, lat: float, width_m: float, height_m: float, angle_deg: float
) -> Polygon:
    """Return a Shapely Polygon for the airport-site rectangle.

    The rectangle is centred at (lon, lat), has the given dimensions in metres,
    and is rotated clockwise from geographic North by angle_deg degrees.

    Coordinate conversion uses a flat-Earth approximation valid for sites ≤ 50 km
    across (well within runway-strip scale anywhere in Brazil).
    """
    lat_rad = math.radians(lat)
    dlon = (width_m / 2) / (111320.0 * math.cos(lat_rad))
    dlat = (height_m / 2) / 111320.0

    # Build axis-aligned rectangle centred at origin
    rect = Polygon([(-dlon, -dlat), (dlon, -dlat), (dlon, dlat), (-dlon, dlat)])
    # Shapely rotate is CCW; clockwise-from-North → negate
    rotated = rotate(rect, -angle_deg, origin=(0.0, 0.0))
    return translate(rotated, xoff=lon, yoff=lat)


def _serialize_assessment(row: dict) -> dict:
    """Maps DB row → MesaAssessment shape expected by the front."""
    created = row.get("created_at")
    return {
        "id": row["id"],
        "siteName": row["site_name"],
        "averageSlope": _to_float(row["average_slope"]),
        "urbanCenterDistance": _to_float(row["urban_center_distance"]),
        "hasObstacles": bool(row["has_obstacles"]),
        "obstacleDescription": row.get("obstacle_description") or "",
        "estimatedCost": _to_float(row["estimated_cost"]),
        "latitude": _to_float(row["latitude"]),
        "longitude": _to_float(row["longitude"]),
        "widthM": _to_float(row.get("width_m", 45.0)),
        "heightM": _to_float(row.get("height_m", 1200.0)),
        "angleDeg": _to_float(row.get("angle_deg", 0.0)),
        "createdAt": created.isoformat() if created else None,
    }


def _score(assessment: dict, weights: dict | None = None) -> dict:
    """Mock scoring (0-100). Each criterion gets a partial score; total is
    a weighted average. Weights default to the front's DEFAULT_ANALYSIS_CONFIG.
    """
    w = weights or {
        "slope": 0.30,
        "distance": 0.25,
        "obstacle": 0.25,
        "cost": 0.20,
    }

    slope = assessment["averageSlope"]
    distance = assessment["urbanCenterDistance"]
    has_obstacles = assessment["hasObstacles"]
    cost = assessment["estimatedCost"]

    # Lower slope = higher score (drops to 0 around 50% slope).
    slope_score = max(0.0, min(100.0, 100.0 - slope * 2.0))
    # Distance: triangular preference around 60km (MESA wants away from cities
    # but not too far). Score peaks at 60 and falls off in both directions.
    distance_score = max(0.0, 100.0 - abs(distance - 60.0) * 1.2)
    obstacle_score = 35.0 if has_obstacles else 90.0
    # Cost normalized assuming 0–500M BRL is the operating range.
    cost_score = max(0.0, min(100.0, 100.0 - (cost / 5_000_000.0)))

    total = (
        slope_score * w["slope"]
        + distance_score * w["distance"]
        + obstacle_score * w["obstacle"]
        + cost_score * w["cost"]
    )

    return {
        "siteName": assessment["siteName"],
        "totalScore": round(total, 1),
        "slopeScore": round(slope_score, 1),
        "distanceScore": round(distance_score, 1),
        "obstacleScore": round(obstacle_score, 1),
        "costScore": round(cost_score, 1),
        "latitude": assessment["latitude"],
        "longitude": assessment["longitude"],
        "widthM": assessment["widthM"],
        "heightM": assessment["heightM"],
        "angleDeg": assessment["angleDeg"],
        "geometry": assessment.get("geometry") or "",
    }


class AssessmentService:
    def __init__(self) -> None:
        self.repo = AssessmentRepository()

    def submit(self, data: dict) -> dict:
        lon = data["longitude"]
        lat = data["latitude"]
        width_m = data.get("widthM", 45.0)
        height_m = data.get("heightM", 1200.0)
        angle_deg = data.get("angleDeg", 0.0)

        polygon = _build_polygon(lon, lat, width_m, height_m, angle_deg)

        row = self.repo.insert(
            site_name=data["siteName"].strip(),
            average_slope=data["averageSlope"],
            urban_center_distance=data["urbanCenterDistance"],
            has_obstacles=data["hasObstacles"],
            obstacle_description=data.get("obstacleDescription") or None,
            estimated_cost=data["estimatedCost"],
            latitude=lat,
            longitude=lon,
            width_m=width_m,
            height_m=height_m,
            angle_deg=angle_deg,
            polygon_wkt=polygon.wkt,
        )
        return _serialize_assessment(row)

    def list_all(self) -> list[dict]:
        return [_serialize_assessment(r) for r in self.repo.get_all()]

    def ranking(self, weights: dict | None = None) -> list[dict]:
        scored = [_score(a, weights) for a in self.list_all()]
        scored.sort(key=lambda r: r["totalScore"], reverse=True)
        return [{"rank": i + 1, **r} for i, r in enumerate(scored)]

    def export_as_shapefile(self, weights: dict | None = None) -> bytes:
        """Builds a real Esri Shapefile (zipped .shp/.dbf/.shx/.prj/.cpg) from
        the current ranking. Each row becomes a POLYGON feature in SIRGAS 2000
        (EPSG:4674) with the assessment scores as attributes.

        Returns the ZIP archive as bytes ready to stream.
        """
        ranking = self.ranking(weights)
        if not ranking:
            raise ValueError("No assessments to export — submit a site first.")

        records = []
        geometries = []
        for r in ranking:
            records.append(
                {
                    "rank": r["rank"],
                    "site_name": r["siteName"][:80],
                    "total": r["totalScore"],
                    "slope": r["slopeScore"],
                    "distance": r["distanceScore"],
                    "obstacle": r["obstacleScore"],
                    "cost": r["costScore"],
                    "lat": r["latitude"],
                    "lon": r["longitude"],
                    "width_m": r["widthM"],
                    "height_m": r["heightM"],
                    "angle_deg": r["angleDeg"],
                }
            )
            # Use the stored polygon geometry; fall back to a centroid point if missing
            if r.get("geometry"):
                geometries.append(shape(json.loads(r["geometry"])))
            else:
                geometries.append(Point(r["longitude"], r["latitude"]))

        gdf = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4674")

        with tempfile.TemporaryDirectory() as work_dir:
            shp_path = os.path.join(work_dir, "mesa_ranking.shp")
            gdf.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname in os.listdir(work_dir):
                    if fname.startswith("mesa_ranking."):
                        zf.write(os.path.join(work_dir, fname), arcname=fname)
            return buf.getvalue()


class AnalysisJobService:
    """In-memory job tracker for the mock MCDA analysis.

    Each /analysis/run call starts a fake job whose progress advances based
    on wall-clock time since submission, so the front's polling loop sees
    realistic 'pending → processing → completed' transitions without us
    needing a real worker queue in Sprint 6.
    """

    _MOCK_DURATION_SEC = 4.0  # job 'finishes' after ~4s of polling

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = Lock()

    def submit(self, config: dict) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "config": config,
                "started_at": time.monotonic(),
            }
        return job_id

    def status(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            elapsed = time.monotonic() - job["started_at"]

        progress = min(100, int((elapsed / self._MOCK_DURATION_SEC) * 100))
        if progress >= 100:
            status = "completed"
        elif progress > 0:
            status = "processing"
        else:
            status = "pending"

        response = {
            "id": job_id,
            "status": status,
            "progress": progress,
        }
        if status == "completed":
            response["resultUrl"] = "/ranking"
        return response
