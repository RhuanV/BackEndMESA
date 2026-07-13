"""Pure mapping tests for Airflow DAG runs → processing-log rows (no network)."""

from geoavia_backend.services.airflow import AirflowTriggerService


def test_map_dag_run_success_computes_duration():
    row = AirflowTriggerService._map_dag_run(
        {
            "dag_id": "load_osm_airports",
            "dag_run_id": "manual__2026-07-13",
            "state": "success",
            "start_date": "2026-07-13T14:00:00+00:00",
            "end_date": "2026-07-13T14:00:12.300000+00:00",
        }
    )
    assert row["job"] == "load_osm_airports"
    assert row["status"] == "completed"
    assert row["duration_ms"] == 12300


def test_map_dag_run_state_translation():
    assert AirflowTriggerService._map_dag_run({"state": "running"})["status"] == "processing"
    assert AirflowTriggerService._map_dag_run({"state": "queued"})["status"] == "processing"
    assert AirflowTriggerService._map_dag_run({"state": "failed"})["status"] == "failed"


def test_map_dag_run_missing_dates_has_no_duration():
    row = AirflowTriggerService._map_dag_run({"dag_id": "x", "state": "running"})
    assert row["duration_ms"] is None
