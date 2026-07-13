"""Health endpoints.

- GET /health: lightweight liveness probe used by start.sh / docker healthcheck.
- GET /health/detailed: role-gated dependency report (DB, Airflow, disk, memory).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import DAG_TRIGGER_ROLES
from geoavia_backend.services import health as health_service

router = APIRouter()


@router.get("/health")
def health():
    """Lightweight liveness probe for start.sh and the dev /health page."""
    return {"status": "ok"}


@router.get("/health/detailed")
def health_detailed(current_user: dict = Depends(require_roles(DAG_TRIGGER_ROLES))):
    """Actionable dependency report: PostgreSQL/PostGIS, Airflow, disk and memory.

    Gated behind an authenticated operational/dev role — never public, so it does
    not leak the system's dependency topology to anonymous callers.
    """
    return health_service.collect()
