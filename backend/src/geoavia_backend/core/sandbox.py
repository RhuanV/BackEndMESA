"""Sandbox mode for the 'desenvolvedor' role.

The developer role can do everything in the system, but its blast radius is
governed by APP_ENV:

  - APP_ENV=sandbox    -> full write access (a non-production environment).
  - APP_ENV=production -> read-only: every mutating request (POST/PUT/PATCH/
    DELETE) from a developer is blocked with 403 and recorded in the audit log.

APP_ENV is read at call time (not import time) so it can be toggled per process
and exercised in tests.
"""
from __future__ import annotations

import logging
import os

from jose import JWTError, jwt

from geoavia_backend.core.database import ALGORITHM, SECRET_KEY
from geoavia_backend.core.roles import DESENVOLVEDOR

audit_logger = logging.getLogger("geoavia.audit")

SANDBOX_ENV = "sandbox"
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def current_env() -> str:
    """Returns the current APP_ENV (defaults to 'production' as a fail-safe)."""
    return os.getenv("APP_ENV", "production").strip().lower()


def is_production() -> bool:
    """True unless APP_ENV is explicitly 'sandbox'."""
    return current_env() != SANDBOX_ENV


def role_from_token(token: str) -> str | None:
    """Best-effort role resolution for a bearer token; None if invalid.

    The token holds only the subject id, so the role is resolved from the
    database — never trusted from the token itself.
    """
    if not SECRET_KEY or not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    sub = payload.get("sub")
    if not sub or not str(sub).isdigit():
        return None
    # Imported lazily to avoid import-time coupling between core and repositories.
    from geoavia_backend.repositories.user import UserRepository

    user = UserRepository().obtain_user_from_id(int(sub))
    return user["role"] if user else None


def developer_write_blocked(role: str | None) -> bool:
    """A developer's writes are blocked only in production (sandbox mode)."""
    return role == DESENVOLVEDOR and is_production()
