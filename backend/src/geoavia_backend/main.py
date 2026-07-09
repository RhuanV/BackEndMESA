"""GeoAvia backend — FastAPI application assembly.

This module only wires the app together: CORS, the sandbox guard and router
registration. Endpoint logic lives in the per-domain routers under
geoavia_backend.api.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from geoavia_backend.core.database import CORS_ORIGINS, FRONTEND_PORT
from geoavia_backend.core.sandbox import (
    WRITE_METHODS,
    audit_logger,
    developer_write_blocked,
    is_production,
    role_from_token,
)

app = FastAPI(title="GeoAvia - Initial Test")

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
    allow_methods=["*"],
    allow_headers=["*"],
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
