"""User-uploaded shapefile endpoints (HU-31)."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import SHAPEFILE_UPLOAD_ROLES
from geoavia_backend.services.shapefiles import ShapefileError, ShapefilesService

router = APIRouter()
shapefiles_service = ShapefilesService()

_require_upload_role = require_roles(SHAPEFILE_UPLOAD_ROLES)

_MAX_MB = int(os.getenv("SHAPEFILE_MAX_UPLOAD_MB", "500"))
SHAPEFILE_MAX_UPLOAD_BYTES = _MAX_MB * 1024 * 1024


@router.post("/shapefiles/upload")
async def upload_shapefile(
    file: UploadFile = File(...),
    layer_name: str = Form(..., min_length=1, max_length=150),
    description: str | None = Form(default=None, max_length=1000),
    current_user: dict = Depends(_require_upload_role),
):
    """Receives a zipped shapefile and ingests it into the mesa_a schema (HU-31).

    The ZIP must contain a single shapefile set (.shp + .dbf + .shx [+ .prj]).
    Geometries are reprojected to SIRGAS 2000 (EPSG:4674).
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload must be a .zip archive")

    zip_bytes = await file.read()
    if len(zip_bytes) > SHAPEFILE_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {SHAPEFILE_MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )

    try:
        return shapefiles_service.import_zip(
            layer_name=layer_name,
            description=description,
            original_filename=file.filename,
            zip_bytes=zip_bytes,
            user_id=int(current_user["sub"]) if current_user.get("sub") else None,
            username=current_user["username"],
            user_role=current_user["role"],
        )
    except ShapefileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/shapefiles")
def list_shapefiles(
    limit: int = 100,
    current_user: dict = Depends(_require_upload_role),
):
    """Lists uploaded shapefiles. Administrators get the full audit view;
    other roles get a version without uploader identity fields."""
    return {
        "uploads": shapefiles_service.list_layers(limit=limit, viewer_role=current_user["role"])
    }


@router.get("/shapefiles/{upload_id}/features")
def get_shapefile_features(
    upload_id: int,
    zoom: str | None = None,
    bbox: str | None = None,
    current_user: dict = Depends(_require_upload_role),
):
    """Returns the upload's features as GeoJSON (for rendering on the map).

    Geometry is simplified per zoom level (z1/z2/z3) and optionally filtered to
    a viewport bbox ('west,south,east,north'), mirroring GET /layers/{name}.
    """
    try:
        return shapefiles_service.fetch_features(upload_id, zoom, bbox)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ShapefileError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
