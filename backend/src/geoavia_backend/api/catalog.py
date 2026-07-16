"""/catalog endpoints — read-only layer metadata catalog (RF01).

Backs the GUI metadata viewer and the (optional) data-catalog page. The
catalog is populated from the metadata spreadsheet by the ingestion service;
these routes only read it. Authenticated; no write routes are exposed here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from geoavia_backend.core.auth import obtain_current_user
from geoavia_backend.repositories.layer_catalog import LayerCatalogRepository

router = APIRouter(prefix="/catalog", dependencies=[Depends(obtain_current_user)])
repo = LayerCatalogRepository()


@router.get("/layers")
def list_catalog_layers(
    tema: str | None = Query(default=None, max_length=120),
    grupo: str | None = Query(default=None, pattern="^(base|analysis|exclusion)$"),
) -> dict:
    """Lists catalog entries, optionally filtered by tema/grupo."""
    return {"layers": repo.list(tema=tema, grupo=grupo)}


@router.get("/layers/{layer_key}")
def get_catalog_layer(layer_key: str) -> dict:
    """Returns a single catalog entry by its layer_key, or 404."""
    entry = repo.get_by_key(layer_key)
    if entry is None:
        raise HTTPException(status_code=404, detail="Layer not found in catalog")
    return entry
