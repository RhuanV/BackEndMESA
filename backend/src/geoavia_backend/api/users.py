"""User management and authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from geoavia_backend.core.auth import obtain_current_user, require_roles
from geoavia_backend.core.database import BOOTSTRAP_USER
from geoavia_backend.core.roles import DESENVOLVEDOR, USER_CREATION_ROLES
from geoavia_backend.schemas.user import (
    PasswordResetRequest,
    RecoveryPasswordResetRequest,
)
from geoavia_backend.services.password_reset import PasswordRecoveryService
from geoavia_backend.services.user import UserService

router = APIRouter()
service = UserService()
recovery_service = PasswordRecoveryService()

_MANAGE_USERS_DETAIL = "Only administrador or desenvolvedor can manage users"


@router.get("/users")
def get_users(current_user: dict = Depends(obtain_current_user)):
    """Returns the list of users through the service and repository layers."""
    return service.list_users()


@router.get("/me")
def get_me(current_user: dict = Depends(obtain_current_user)):
    """Returns the authenticated user's identity, resolved server-side.

    The client relies on this (not on decoding the token) to know who it is and
    which role governs the UI.
    """
    return {"username": current_user["username"], "role": current_user["role"]}


@router.post("/users/signup")
def create_user(
    username: str,
    role: str = "operador",
    current_user: dict = Depends(
        require_roles(USER_CREATION_ROLES, detail=_MANAGE_USERS_DETAIL)
    ),
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
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates the user and returns a JWT access token."""
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        # Minimal token: only the subject id. Username/role are resolved from the
        # database on every request (see obtain_current_user), so nothing
        # sensitive or stale is carried in the token.
        access_token = service.security.create_access_token({"sub": str(user["id"])})
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"access_token": access_token, "token_type": "bearer"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(
        require_roles(USER_CREATION_ROLES, detail=_MANAGE_USERS_DETAIL)
    ),
):
    """Removes a user by ID."""
    deleted = service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

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
    current_user: dict = Depends(
        require_roles(USER_CREATION_ROLES, detail=_MANAGE_USERS_DETAIL)
    ),
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
def reset_password_with_code(payload: RecoveryPasswordResetRequest):
    """Public: resets a password using an admin-issued recovery code.

    Errors are intentionally generic to avoid revealing whether a username or
    code exists.
    """
    try:
        recovery_service.reset_with_code(
            payload.username, payload.code, payload.new_password
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Password was successfully changed"}
