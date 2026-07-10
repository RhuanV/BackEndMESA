"""Endpoints for triggering and auditing Airflow DAGs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import DAG_TRIGGER_ROLES
from geoavia_backend.services.airflow import (
    AirflowTriggerError,
    AirflowTriggerService,
    UnknownDagError,
)

router = APIRouter()
airflow_trigger_service = AirflowTriggerService()


@router.post("/airflow/trigger/{dag_id}")
def trigger_airflow_dag(
    dag_id: str,
    current_user: dict = Depends(
        require_roles(DAG_TRIGGER_ROLES, detail="Permission denied for DAG trigger")
    ),
):
    """Triggers a whitelisted Airflow DAG and audits who triggered it.

    Available DAGs: see ALLOWED_DAGS in services.airflow.
    """
    try:
        return airflow_trigger_service.trigger(
            dag_id=dag_id,
            user_id=int(current_user["sub"]) if current_user.get("sub") else None,
            username=current_user["username"],
            user_role=current_user["role"],
        )
    except UnknownDagError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AirflowTriggerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/airflow/triggers")
def list_airflow_triggers(
    limit: int = 100,
    current_user: dict = Depends(require_roles(DAG_TRIGGER_ROLES)),
):
    """Returns the most recent manual DAG triggers (audit log)."""
    return {
        "allowed_dags": airflow_trigger_service.list_allowed_dags(),
        "recent": airflow_trigger_service.list_recent_logs(limit=limit),
    }
