"""/cases endpoints — Caso/Projeto domain and lifecycle (UML / Arquitetura).

Gates:
- create: CASE_CREATE_ROLES (Gestor opens the case and sets the Coordenador)
- read/link sites: CASE_EXECUTE_ROLES (Operador and above)
- update / status transition: CASE_MANAGE_ROLES (Coordenador / admin)

Status transitions and site links are audited.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import (
    CASE_CREATE_ROLES,
    CASE_EXECUTE_ROLES,
    CASE_MANAGE_ROLES,
)
from geoavia_backend.schemas.projeto import (
    LinkSiteRequest,
    ProjetoCreateRequest,
    ProjetoUpdateRequest,
    StatusChangeRequest,
)
from geoavia_backend.services import audit as audit_actions
from geoavia_backend.services.audit import AuditService
from geoavia_backend.services.projeto import ProjetoService

router = APIRouter(prefix="/cases")
service = ProjetoService()
audit_service = AuditService()

_require_create = require_roles(CASE_CREATE_ROLES, detail="Only a case manager can create cases")
_require_manage = require_roles(CASE_MANAGE_ROLES, detail="Only a case manager can manage cases")
_require_read = require_roles(CASE_EXECUTE_ROLES, detail="Authentication required")


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _user_id(current_user: dict) -> int | None:
    sub = str(current_user.get("sub", ""))
    return int(sub) if sub.isdigit() else None


@router.post("")
def create_case(
    request: Request,
    payload: ProjetoCreateRequest,
    current_user: dict = Depends(_require_create),
):
    try:
        case = service.create(payload.model_dump(), current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service.record(
        action=audit_actions.CASE_CREATE,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(case["id"]),
        detail=f"Created case '{case['nome']}'",
        ip_address=_client_ip(request),
    )
    return case


@router.get("")
def list_cases(
    status: str | None = Query(default=None, pattern="^(iniciado|em_analise|campo|concluido)$"),
    current_user: dict = Depends(_require_read),
):
    return {"cases": service.list(status=status)}


@router.get("/{case_id}")
def get_case(case_id: int, current_user: dict = Depends(_require_read)):
    case = service.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}")
def update_case(
    request: Request,
    case_id: int,
    payload: ProjetoUpdateRequest,
    current_user: dict = Depends(_require_manage),
):
    try:
        case = service.update(case_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    audit_service.record(
        action=audit_actions.CASE_UPDATE,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(case_id),
        detail=f"Updated case id {case_id}",
        ip_address=_client_ip(request),
    )
    return case


@router.post("/{case_id}/status")
def change_case_status(
    request: Request,
    case_id: int,
    payload: StatusChangeRequest,
    current_user: dict = Depends(_require_manage),
):
    try:
        case = service.change_status(case_id, payload.status, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service.record(
        action=audit_actions.CASE_STATUS_CHANGE,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(case_id),
        detail=f"{case['previousStatus']} → {case['status']}",
        ip_address=_client_ip(request),
    )
    return case


@router.get("/{case_id}/sites")
def list_case_sites(case_id: int, current_user: dict = Depends(_require_read)):
    if service.get(case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"sites": service.list_sites(case_id)}


@router.post("/{case_id}/sites")
def link_case_site(
    request: Request,
    case_id: int,
    payload: LinkSiteRequest,
    current_user: dict = Depends(_require_read),
):
    try:
        result = service.link_site(case_id, payload.assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service.record(
        action=audit_actions.CASE_SITE_LINK,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(case_id),
        detail=f"Linked assessment {payload.assessment_id} to case {case_id}",
        ip_address=_client_ip(request),
    )
    return result
