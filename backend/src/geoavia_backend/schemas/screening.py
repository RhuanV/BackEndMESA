"""Pydantic request models for the screening endpoint."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ScreeningRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    target_municipality_ibge_code: str = Field(
        min_length=7, max_length=7, pattern=r"^[0-9]{7}$"
    )
