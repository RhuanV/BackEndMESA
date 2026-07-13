"""Processing logs endpoint: real DAG runs (Airflow) + persisted backend jobs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import DAG_TRIGGER_ROLES
from geoavia_backend.repositories.processing import ProcessingLogRepository
from geoavia_backend.services.airflow import AirflowTriggerError, AirflowTriggerService

router = APIRouter()
airflow_service = AirflowTriggerService()
processing_repo = ProcessingLogRepository()


@router.get("/processing-logs")
def get_processing_logs(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(require_roles(DAG_TRIGGER_ROLES)),
):
    """Returns real processing history from two sources:

    - `airflow_runs`: recent DAG runs (data-ingestion pipeline).
    - `jobs`: backend MCDA jobs persisted in processing_log.

    If Airflow is unreachable the page still works: `airflow_runs` is empty and
    `airflow_error` carries the reason instead of failing the whole request.
    """
    airflow_error: str | None = None
    try:
        airflow_runs = airflow_service.list_dag_runs(limit=limit)
    except AirflowTriggerError as exc:
        airflow_runs = []
        airflow_error = str(exc)

    return {
        "airflow_runs": airflow_runs,
        "airflow_error": airflow_error,
        "jobs": processing_repo.list_recent(limit=limit),
    }
