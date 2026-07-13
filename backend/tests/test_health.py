"""Aggregation logic for the detailed health report (no DB/network)."""

from geoavia_backend.services import health


def test_all_ok_is_ok():
    checks = [
        {"name": "PostgreSQL/PostGIS", "status": "ok"},
        {"name": "Airflow", "status": "ok"},
        {"name": "Disco", "status": "ok"},
    ]
    assert health.aggregate_status(checks) == "ok"


def test_database_failure_is_critical_error():
    checks = [
        {"name": "PostgreSQL/PostGIS", "status": "error"},
        {"name": "Airflow", "status": "ok"},
    ]
    assert health.aggregate_status(checks) == "error"


def test_non_critical_failure_only_degrades():
    checks = [
        {"name": "PostgreSQL/PostGIS", "status": "ok"},
        {"name": "Airflow", "status": "error"},
        {"name": "Memória", "status": "unknown"},
    ]
    assert health.aggregate_status(checks) == "degraded"
