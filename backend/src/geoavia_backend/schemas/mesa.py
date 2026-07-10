"""Pydantic request models for the MESA (assessment/analysis) endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssessmentIn(BaseModel):
    siteName: str = Field(min_length=3, max_length=100)
    averageSlope: float = Field(ge=0, le=100)
    urbanCenterDistance: float = Field(ge=0, le=10000)
    hasObstacles: bool
    obstacleDescription: str | None = Field(default=None, max_length=500)
    estimatedCost: float = Field(ge=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    widthM: float = Field(default=45.0, ge=1, le=10000)
    heightM: float = Field(default=1200.0, ge=1, le=50000)
    angleDeg: float = Field(default=0.0, ge=0, lt=360)


class AnalysisConfigIn(BaseModel):
    slopeWeight: float = Field(ge=0, le=100)
    slopeThreshold: float = Field(ge=0, le=45)
    landUseWeight: float = Field(ge=0, le=100)
    transportWeight: float = Field(ge=0, le=100)
    transportBufferKm: float = Field(ge=0, le=500)
    costWeight: float = Field(ge=0, le=100)
    applyExclusions: bool
