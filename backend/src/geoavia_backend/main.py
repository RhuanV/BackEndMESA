"""GeoAvia backend — FastAPI application assembly.

This module only wires the app together: CORS, the sandbox guard and router
registration. Endpoint logic lives in the per-domain routers under
geoavia_backend.api.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from geoavia_backend.api import (
    airflow,
    health,
    layers,
    mesa,
    regions,
    screening,
    shapefiles,
    users,
)
from geoavia_backend.core.database import APP_ENV, CORS_ORIGINS, FRONTEND_PORT, SECRET_KEY
from geoavia_backend.core.rate_limit import limiter
from geoavia_backend.core.sandbox import (
    WRITE_METHODS,
    audit_logger,
    developer_write_blocked,
    is_production,
    role_from_token,
)

logger = logging.getLogger("geoavia.startup")

# Placeholder shipped in .env_example — must never be used as a real signing key.
_PLACEHOLDER_SECRET = "change_for_a_strong_password"


def _validate_secret_key() -> None:
    """Fails fast in production if the JWT signing key is missing or the default.

    Runs at server startup (not import time), so tests and OpenAPI generation are
    unaffected. In sandbox a weak key only warns, keeping local dev friction-free.
    """
    weak = (not SECRET_KEY) or SECRET_KEY == _PLACEHOLDER_SECRET
    if not weak:
        return
    if APP_ENV == "production":
        raise RuntimeError(
            "SECRET_KEY is missing or still the placeholder. Set a strong, unique "
            "SECRET_KEY in .env before running in production (e.g. "
            "`python -c 'import secrets; print(secrets.token_urlsafe(48))'`)."
        )
    logger.warning(
        "SECRET_KEY is weak/placeholder in APP_ENV=%s. This is fine for local "
        "development, but set a strong SECRET_KEY before production.",
        APP_ENV,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _validate_secret_key()
    yield


app = FastAPI(title="GeoAvia - Initial Test", lifespan=lifespan)

# Rate limiting (slowapi): the limiter is attached to the app and its 429
# handler registered here; individual routes opt in with @limiter.limit(...).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allowed origins: explicit CORS_ORIGINS if configured, otherwise the local
# frontend only (never a wildcard, since credentials are allowed).
allowed_origins = CORS_ORIGINS or [
    f"http://localhost:{FRONTEND_PORT}",
    f"http://127.0.0.1:{FRONTEND_PORT}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    # Explicit allowlist instead of wildcards: only the methods and headers the
    # frontend actually uses.
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def sandbox_guard(request: Request, call_next):
    """Enforces sandbox mode: the 'desenvolvedor' role is read-only in
    production. Every developer write attempt is audited; in production it is
    also blocked with 403. In sandbox the developer keeps full access."""
    if request.method in WRITE_METHODS:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            role = role_from_token(auth[7:])
            if role == "desenvolvedor":
                audit_logger.info(
                    "developer write %s %s (production=%s)",
                    request.method,
                    request.url.path,
                    is_production(),
                )
                if developer_write_blocked(role):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": (
                                "Developer role is read-only in production "
                                "(sandbox mode). Use an administrador account, "
                                "or set APP_ENV=sandbox in a non-production "
                                "environment."
                            )
                        },
                    )
    return await call_next(request)


app.include_router(health.router)
app.include_router(users.router)
app.include_router(layers.router)
app.include_router(screening.router)
app.include_router(airflow.router)
app.include_router(shapefiles.router)
app.include_router(mesa.router)
app.include_router(regions.router)
