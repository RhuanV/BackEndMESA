"""Map layer endpoints — GeoJSON delivery and fallback source configuration."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from geoavia_backend.core.auth import obtain_current_user, require_roles
from geoavia_backend.core.roles import LAYER_SOURCE_ROLES
from geoavia_backend.services.layers import LayersService

router = APIRouter()
layers_service = LayersService()


@router.get("/layers/{layer_name}")
def get_layer(
    layer_name: str,
    zoom: str | None = None,
    bbox: str | None = None,
    current_user: dict = Depends(obtain_current_user),
):
    """Returns the requested layer as GeoJSON, simplified per zoom level.

    See LAYER_REGISTRY in services.layers for the allowed layer names.
    """
    try:
        return layers_service.fetch(layer_name, zoom, bbox)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/layers/{layer_name}/source")
def get_layer_source(
    layer_name: str,
    current_user: dict = Depends(obtain_current_user),
):
    """Returns the upload configured as fallback data source for this layer."""
    try:
        return layers_service.get_source(layer_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/layers/{layer_name}/source")
def set_layer_source(
    layer_name: str,
    upload_id: int | None = None,
    current_user: dict = Depends(require_roles(LAYER_SOURCE_ROLES)),
):
    """Sets (or clears) the upload that feeds this layer when Airflow data is absent."""
    try:
        layers_service.set_source(layer_name, upload_id)
        return {"ok": True, "layer_name": layer_name, "upload_id": upload_id}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
