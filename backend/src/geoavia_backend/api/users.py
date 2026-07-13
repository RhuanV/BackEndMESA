"""User management and authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from geoavia_backend.core.auth import obtain_current_user, require_roles
from geoavia_backend.core.database import APP_ENV, BOOTSTRAP_USER
from geoavia_backend.core.rate_limit import limiter
from geoavia_backend.core.roles import DESENVOLVEDOR, USER_CREATION_ROLES
from geoavia_backend.repositories.user import UserRepository
from geoavia_backend.schemas.user import (
    PasswordResetRequest,
    RecoveryPasswordResetRequest,
)
from geoavia_backend.services.audit import AuditService
from geoavia_backend.services.password_reset import PasswordRecoveryService
from geoavia_backend.services.user import REFRESH_TOKEN_EXPIRE_DAYS, UserService

# Refresh token lives in an httpOnly cookie; access tokens travel as Bearer.
_REFRESH_COOKIE = "geoavia_refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=(APP_ENV == "production"),
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/")


router = APIRouter()
service = UserService()
recovery_service = PasswordRecoveryService()
audit_service = AuditService()


def _client_ip(request: Request) -> str | None:
    """Best-effort client IP for the audit log (no proxy header trust)."""
    return request.client.host if request.client else None


_MANAGE_USERS_DETAIL = "Only administrador or desenvolvedor can manage users"
# Single dependency instance reused by the user-management routes.
_require_manage_users = require_roles(USER_CREATION_ROLES, detail=_MANAGE_USERS_DETAIL)


@router.get("/users")
def get_users(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(obtain_current_user),
):
    """Returns a paginated list of users (defaults: first 100)."""
    return service.list_users(limit=limit, offset=offset)


@router.get("/me")
def get_me(current_user: dict = Depends(obtain_current_user)):
    """Returns the authenticated user's identity, resolved server-side.

    The client relies on this (not on decoding the token) to know who it is and
    which role governs the UI.
    """
    return {"username": current_user["username"], "role": current_user["role"]}


@router.post("/users/signup")
def create_user(
    request: Request,
    username: str,
    role: str = "operador",
    current_user: dict = Depends(_require_manage_users),
):
    """Creates a user (administrador/desenvolvedor only) for the first-access flow.

    The admin does not set a password: the account is created without a usable
    password and a single-use first-access code is returned so the admin can
    relay it. The user sets their own password via POST /password-reset.

    Only a desenvolvedor may grant the privileged 'desenvolvedor' role.
    """
    if role.strip().lower() == DESENVOLVEDOR and current_user["role"] != DESENVOLVEDOR:
        raise HTTPException(
            status_code=403,
            detail="Only a desenvolvedor can grant the 'desenvolvedor' role.",
        )

    issued_by = int(current_user["sub"]) if str(current_user.get("sub", "")).isdigit() else None
    try:
        new_id = service.create_pending_user(username, role)
        result = recovery_service.issue_code(new_id, issued_by)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service.record(
        action="USER_CREATE",
        user_id=issued_by,
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(new_id),
        detail=f"Created user '{username.strip()}' with role '{role.strip().lower()}'",
        ip_address=_client_ip(request),
    )

    return {
        "id": new_id,
        "code": result["code"],
        "expires_at": result["expires_at"],
        "message": (
            "User created. Relay this first-access code so they can set their "
            "password on the login screen; it can be used once."
        ),
    }


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates the user, returns a short-lived access token (JSON) and sets
    a long-lived refresh token in an httpOnly cookie.

    Rate-limited per IP to slow down brute-force/credential-stuffing attempts.
    """
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        # Security event: record the attempt (username only, never the password).
        audit_service.record(
            action="LOGIN_FAILED",
            username=form_data.username[:50] if form_data.username else None,
            detail="Invalid credentials",
            ip_address=_client_ip(request),
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    audit_service.record(
        action="LOGIN",
        user_id=user["id"],
        username=user["username"],
        user_role=user["role"],
        detail="Login successful",
        ip_address=_client_ip(request),
    )

    try:
        # Tokens carry only the subject id; username/role are resolved from the
        # database on every request (see obtain_current_user).
        sub = str(user["id"])
        access_token = service.security.create_access_token(sub)
        refresh_token = service.security.create_refresh_token(sub)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _set_refresh_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
@limiter.limit("30/minute")
def refresh(request: Request, response: Response):
    """Issues a new access token from the refresh cookie and rotates the cookie.

    Uses only the httpOnly cookie (no Bearer). Generic 401 if it is missing,
    invalid, expired, or the user no longer exists.
    """
    invalid = HTTPException(status_code=401, detail="Invalid or expired session")
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise invalid

    sub = service.security.decode_refresh_subject(token)
    if not sub:
        raise invalid
    if UserRepository().obtain_user_from_id(int(sub)) is None:
        _clear_refresh_cookie(response)
        raise invalid

    access_token = service.security.create_access_token(sub)
    _set_refresh_cookie(response, service.security.create_refresh_token(sub))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, response: Response):
    """Clears the refresh cookie, ending the session."""
    # Best-effort: resolve who is logging out from the refresh cookie (never trusted
    # for auth here — used only to label the audit entry).
    token = request.cookies.get(_REFRESH_COOKIE)
    sub = service.security.decode_refresh_subject(token) if token else None
    user = UserRepository().obtain_user_from_id(int(sub)) if sub else None
    audit_service.record(
        action="LOGOUT",
        user_id=user["id"] if user else None,
        username=user["username"] if user else None,
        user_role=user["role"] if user else None,
        detail="Logout",
        ip_address=_client_ip(request),
    )
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.delete("/users/{user_id}")
def delete_user(
    request: Request,
    user_id: int,
    current_user: dict = Depends(_require_manage_users),
):
    """Removes a user by ID."""
    deleted = service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    audit_service.record(
        action="USER_DELETE",
        user_id=int(current_user["sub"]) if str(current_user.get("sub", "")).isdigit() else None,
        username=current_user["username"],
        user_role=current_user["role"],
        resource=str(user_id),
        detail=f"Deleted user id {user_id}",
        ip_address=_client_ip(request),
    )
    return {"message": "User was successfully deleted"}


@router.put("/users/{user_id}/password")
def change_password(
    user_id: int,
    payload: PasswordResetRequest,
    current_user: dict = Depends(obtain_current_user),
):
    """Resets the password for a user. Available only to the protected bootstrap user."""
    if current_user["username"] != BOOTSTRAP_USER:
        raise HTTPException(
            status_code=403,
            detail="Only the protected bootstrap user can reset passwords through this route.",
        )

    try:
        updated = service.change_password(user_id, payload.new_password)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Password was successfully changed"}


@router.post("/users/{user_id}/recovery-code")
def issue_recovery_code(
    user_id: int,
    current_user: dict = Depends(_require_manage_users),
):
    """Issues a single-use, time-limited password-recovery code for a user.

    Returns the code once so the administrator can relay it to the user; only
    its hash is stored. The user redeems it via POST /password-reset.
    """
    issued_by = int(current_user["sub"]) if str(current_user.get("sub", "")).isdigit() else None
    try:
        result = recovery_service.issue_code(user_id, issued_by)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "code": result["code"],
        "expires_at": result["expires_at"],
        "message": "Recovery code generated. Relay it to the user; it can be used once.",
    }


@router.post("/password-reset")
@limiter.limit("5/minute")
def reset_password_with_code(request: Request, payload: RecoveryPasswordResetRequest):
    """Public: resets a password using an admin-issued recovery code.

    Rate-limited per IP. Errors are intentionally generic to avoid revealing
    whether a username or code exists.
    """
    try:
        recovery_service.reset_with_code(payload.username, payload.code, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Password was successfully changed"}
