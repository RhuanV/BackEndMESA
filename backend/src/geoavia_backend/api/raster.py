"""/raster endpoints — MCDA suitability overlay for the web map (Fase 5).

Serves the computed suitability raster as a colorized PNG (with its geographic
bounds) so the frontend can drop it onto MapLibre as an image overlay, plus a
JSON metadata route (bounds + ranked points). Authenticated; the suitability is
computed/cached by ``services.raster.RasterService``.
"""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from geoavia_backend.core.auth import obtain_current_user
from geoavia_backend.services.raster import RasterDataUnavailable, RasterService

router = APIRouter(prefix="/raster", dependencies=[Depends(obtain_current_user)])
service = RasterService()


def _config(
    slope_weight: float,
    land_use_weight: float,
    transport_weight: float,
    cost_weight: float,
    slope_threshold: float,
    apply_exclusions: bool,
) -> dict:
    return {
        "slopeWeight": slope_weight,
        "landUseWeight": land_use_weight,
        "transportWeight": transport_weight,
        "costWeight": cost_weight,
        "slopeThreshold": slope_threshold,
        "applyExclusions": apply_exclusions,
    }


@router.get("/suitability/{codigo_ibge}")
def suitability_meta(
    codigo_ibge: str,
    slope_weight: float = Query(default=30.0, ge=0, le=100),
    land_use_weight: float = Query(default=25.0, ge=0, le=100),
    transport_weight: float = Query(default=25.0, ge=0, le=100),
    cost_weight: float = Query(default=20.0, ge=0, le=100),
    slope_threshold: float = Query(default=2.0, ge=0, le=45),
    apply_exclusions: bool = Query(default=True),
) -> JSONResponse:
    """Returns the suitability bounds + ranked candidate points (JSON)."""
    config = _config(
        slope_weight,
        land_use_weight,
        transport_weight,
        cost_weight,
        slope_threshold,
        apply_exclusions,
    )
    try:
        result = service.compute_suitability(codigo_ibge, config)
    except RasterDataUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return JSONResponse(
        {
            "codigoIbge": codigo_ibge,
            "bounds": result["bounds"],
            "ranked": result["ranked"],
            "pngUrl": f"/raster/suitability/{codigo_ibge}.png",
        }
    )


@router.get("/suitability/{codigo_ibge}.png")
def suitability_png(
    codigo_ibge: str,
    slope_weight: float = Query(default=30.0, ge=0, le=100),
    land_use_weight: float = Query(default=25.0, ge=0, le=100),
    transport_weight: float = Query(default=25.0, ge=0, le=100),
    cost_weight: float = Query(default=20.0, ge=0, le=100),
    slope_threshold: float = Query(default=2.0, ge=0, le=45),
    apply_exclusions: bool = Query(default=True),
) -> StreamingResponse:
    """Returns the colorized suitability PNG for the map overlay.

    The bounds needed to georeference the image are exposed via the
    ``X-Raster-Bounds`` header (also available at the JSON route above).
    """
    config = _config(
        slope_weight,
        land_use_weight,
        transport_weight,
        cost_weight,
        slope_threshold,
        apply_exclusions,
    )
    try:
        png, bounds = service.render_suitability_png(codigo_ibge, config)
    except RasterDataUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return StreamingResponse(
        BytesIO(png),
        media_type="image/png",
        headers={"X-Raster-Bounds": ",".join(str(b) for b in bounds)},
    )
