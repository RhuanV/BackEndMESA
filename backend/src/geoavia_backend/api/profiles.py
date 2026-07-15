"""/profiles endpoints — CRUD for custom permission profiles (Perfis).

Admin-gated by the `admin:profiles` permission. System profiles (seeded from
the base roles) are read-only. The permission catalog is exposed so the UI can
render the available permissions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from geoavia_backend.core.auth import require_permissions
from geoavia_backend.core.permissions import ADMIN_PROFILES, ALL_PERMISSIONS
from geoavia_backend.schemas.profile import ProfileCreateRequest, ProfileUpdateRequest
from geoavia_backend.services import audit as audit_actions
from geoavia_backend.services.audit import AuditService
from geoavia_backend.services.profile import ProfileService

router = APIRouter(prefix="/profiles")
service = ProfileService()
audit_service = AuditService()

_MANAGE_DETAIL = "Only users with admin:profiles can manage permission profiles"
_require_manage = require_permissions({ADMIN_PROFILES}, detail=_MANAGE_DETAIL)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _user_id(current_user: dict) -> int | None:
    sub = str(current_user.get("sub", ""))
    return int(sub) if sub.isdigit() else None


@router.get("/permissions")
def list_permissions(current_user: dict = Depends(_require_manage)) -> dict:
    """Returns the catalog of assignable permission strings."""
    return {"permissions": sorted(ALL_PERMISSIONS)}


@router.get("")
def list_profiles(current_user: dict = Depends(_require_manage)) -> dict:
    return {"profiles": service.list_profiles()}


@router.post("")
def create_profile(
    request: Request,
    payload: ProfileCreateRequest,
    current_user: dict = Depends(_require_manage),
) -> dict:
    try:
        new_id = service.create_profile(payload.name, payload.description, payload.permissions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service.record(
        action=audit_actions.PROFILE_CREATE,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(new_id),
        detail=f"Created profile '{payload.name.strip()}'",
        ip_address=_client_ip(request),
    )
    return {"id": new_id, "message": "Profile created"}


@router.patch("/{profile_id}")
def update_profile(
    request: Request,
    profile_id: int,
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(_require_manage),
) -> dict:
    try:
        updated = service.update_profile(profile_id, payload.description, payload.permissions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Profile not found")

    audit_service.record(
        action=audit_actions.PROFILE_UPDATE,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(profile_id),
        detail=f"Updated profile id {profile_id}",
        ip_address=_client_ip(request),
    )
    return {"message": "Profile updated"}


@router.delete("/{profile_id}")
def delete_profile(
    request: Request,
    profile_id: int,
    current_user: dict = Depends(_require_manage),
) -> dict:
    try:
        deleted = service.delete_profile(profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")

    audit_service.record(
        action=audit_actions.PROFILE_DELETE,
        user_id=_user_id(current_user),
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(profile_id),
        detail=f"Deleted profile id {profile_id}",
        ip_address=_client_ip(request),
    )
    return {"message": "Profile deleted"}
