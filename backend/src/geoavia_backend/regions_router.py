"""Endpoints /regions — lookup hierárquico de estados e municípios (RF02).

Read-only, autenticado. Usado pelo MunicipalitySelector do front pra montar
dropdowns dependentes sem puxar geometria.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException

from geoavia_backend.auth_dep import obtain_current_user
from geoavia_backend.regions_repository import RegionsRepository

router = APIRouter(prefix="/regions", dependencies=[Depends(obtain_current_user)])
repo = RegionsRepository()

_UF_PATTERN = re.compile(r"^[A-Z]{2}$")


@router.get("/states")
def list_states() -> dict:
    """Returns all states. Lightweight — no geometry."""
    states = repo.list_states()
    return {"states": states}


@router.get("/states/{sigla}/municipalities")
def list_municipalities(sigla: str) -> dict:
    """Returns the municipalities of the given UF, sorted by name."""
    normalized = sigla.upper()
    if not _UF_PATTERN.match(normalized):
        raise HTTPException(
            status_code=400, detail="sigla must be a 2-letter UF code (e.g. SP)"
        )
    municipalities = repo.list_municipalities_by_state(normalized)
    return {"sigla_estado": normalized, "municipalities": municipalities}
