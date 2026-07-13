"""Smoke tests for the FastAPI app assembly.

Verifies the app imports and that every expected route is registered after the
package reorganization (routers split under geoavia_backend.api). No network or
DB access — inspects the generated OpenAPI schema only.
"""

from __future__ import annotations

from geoavia_backend.main import app

EXPECTED_PATHS = {
    "/health",
    "/audit-logs",
    "/processing-logs",
    "/users",
    "/users/signup",
    "/login",
    "/refresh",
    "/logout",
    "/me",
    "/users/{user_id}",
    "/users/{user_id}/password",
    "/users/{user_id}/recovery-code",
    "/password-reset",
    "/layers/{layer_name}",
    "/layers/{layer_name}/source",
    "/screening",
    "/airflow/trigger/{dag_id}",
    "/airflow/triggers",
    "/shapefiles/upload",
    "/shapefiles",
    "/shapefiles/{upload_id}/features",
    "/assessments",
    "/ranking",
    "/analysis/run",
    "/analysis/status/{job_id}",
    "/export/{format}",
    "/regions/states",
    "/regions/states/{sigla}/municipalities",
}


def test_app_imports():
    assert app.title == "GeoAvia - Initial Test"


def test_all_expected_routes_registered():
    registered = set(app.openapi()["paths"].keys())
    missing = EXPECTED_PATHS - registered
    assert not missing, f"Missing routes after reorg: {sorted(missing)}"
