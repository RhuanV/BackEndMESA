"""Read-only endpoint for the security/action audit log (admin-gated)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import ADMIN_ROLES
from geoavia_backend.services.audit import AuditService

router = APIRouter()
audit_service = AuditService()

_require_admin = require_roles(
    ADMIN_ROLES, detail="Only administrador or desenvolvedor can read the audit log"
)


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None, max_length=40),
    username: str | None = Query(default=None, max_length=50),
    current_user: dict = Depends(_require_admin),
):
    """Returns the most recent audit entries (newest first), with optional filters.

    The log is append-only: this router exposes no write/update/delete route.
    """
    return audit_service.repo.list_recent(
        limit=limit, offset=offset, action=action, username=username
    )
