"""User management and authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from geoavia_backend.core.auth import obtain_current_user, require_roles
from geoavia_backend.core.database import DEV_USER
from geoavia_backend.core.roles import USER_CREATION_ROLES
from geoavia_backend.schemas.user import PasswordResetRequest, UpdateUsernameRequest
from geoavia_backend.services.user import UserService

router = APIRouter()
service = UserService()


@router.get("/users")
def get_users(current_user: dict = Depends(obtain_current_user)):
    """Returns the list of users through the service and repository layers."""
    return service.list_users()


@router.post("/users/signup")
def create_user(
    username: str,
    password: str,
    role: str = "operador",
    current_user: dict = Depends(
        require_roles(USER_CREATION_ROLES, detail="Only coordenador and supervisor can create users")
    ),
):
    """Creates a user (coordenador/supervisor only)."""
    try:
        new_id = service.register_user(username, password, role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"id": new_id, "message": "User was successfully created"}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticates the user and returns a JWT access token."""
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        access_token = service.security.create_access_token(
            {
                "sub": str(user["id"]),
                "username": user["username"],
                "role": user["role"],
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/users/{user_id}/username")
def update_username(
    user_id: int,
    payload: UpdateUsernameRequest,
    current_user: dict = Depends(
        require_roles(USER_CREATION_ROLES, detail="Only coordenador and supervisor can change usernames")
    ),
):
    """Updates a user's username."""
    try:
        updated = service.change_username(user_id, payload.username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Username was successfully changed"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(
        require_roles(USER_CREATION_ROLES, detail="Only coordenador and supervisor can delete users")
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
    """Resets the password for a user. Available only to DEV_USER."""
    if current_user["username"] != DEV_USER:
        raise HTTPException(
            status_code=403,
            detail="Only the main developer can reset passwords through this route.",
        )

    try:
        updated = service.change_password(user_id, payload.new_password)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Password was successfully changed"}
