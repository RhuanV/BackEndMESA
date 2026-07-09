"""GeoAvia backend — FastAPI application assembly.

This module only wires the app together: CORS + router registration. Endpoint
logic lives in the per-domain routers under geoavia_backend.api.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from geoavia_backend.core.database import FRONTEND_PORT

app = FastAPI(title="GeoAvia - Initial Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{FRONTEND_PORT}",
        f"http://127.0.0.1:{FRONTEND_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(layers.router)
app.include_router(screening.router)
app.include_router(airflow.router)
app.include_router(shapefiles.router)
app.include_router(mesa.router)
app.include_router(regions.router)
