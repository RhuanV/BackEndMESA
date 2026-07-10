"""Spatial screening endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from geoavia_backend.core.auth import require_roles
from geoavia_backend.core.roles import SCREENING_ROLES
from geoavia_backend.schemas.screening import ScreeningRequest
from geoavia_backend.services.screening import LayersNotReadyError, ScreeningService

router = APIRouter()
screening_service = ScreeningService()


@router.post("/screening")
def screen_site(
    payload: ScreeningRequest,
    current_user: dict = Depends(
        require_roles(SCREENING_ROLES, detail="You do not have permission to run the screening")
    ),
):
    """Spatial screening — classifies a point as viavel / intermediario /
    restrito based on (a) containment within the target municipality, (b) intersection
    with restrictive infrastructure layers, and (c) proximity within protective buffers.
    """
    try:
        return screening_service.screen(
            payload.latitude,
            payload.longitude,
            payload.target_municipality_ibge_code,
        )
    except LayersNotReadyError as exc:
        raise HTTPException(
            status_code=503,
            detail={"message": str(exc), "missing_layers": exc.missing_layers},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
