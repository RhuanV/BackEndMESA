"""Shared authentication dependencies for FastAPI routers."""
from collections.abc import Callable, Iterable

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from geoavia_backend.core.database import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def obtain_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validates the JWT token and returns the basic data of the authenticated user."""
    unauthorized_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY not found in .env")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        if not sub or not username or not role:
            raise unauthorized_exception
    except JWTError as exc:
        raise unauthorized_exception from exc

    return {"sub": sub, "username": username, "role": role}


def require_roles(
    roles: Iterable[str],
    detail: str = "Permission denied",
) -> Callable[..., dict]:
    """Dependency factory: authenticates the user and enforces role membership.

    Returns the authenticated user dict, or raises 403 (with `detail`) if their
    role is not in `roles`.
    """
    allowed = set(roles)

    def dependency(current_user: dict = Depends(obtain_current_user)) -> dict:
        if current_user["role"] not in allowed:
            raise HTTPException(status_code=403, detail=detail)
        return current_user

    return dependency
