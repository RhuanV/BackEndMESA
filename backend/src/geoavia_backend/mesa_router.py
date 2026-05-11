"""Endpoints MESA — Sprint 2.

Cobre o que o front já consome via apiClient (ver
frontend/src/features/{assessment,analysis,results}/services). Tudo aqui
roda em modo mock pra o demo da Sprint 2; os épicos EP-12 (critérios
classificatórios reais) e EP-13 (AHP/AIP integrado) substituem isso depois.
"""
from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from geoavia_backend.auth_dep import obtain_current_user
from geoavia_backend.mesa_service import AnalysisJobService, AssessmentService

router = APIRouter(dependencies=[Depends(obtain_current_user)])
assessment_service = AssessmentService()
analysis_service = AnalysisJobService()


class AssessmentIn(BaseModel):
    siteName: str = Field(min_length=3, max_length=100)
    averageSlope: float = Field(ge=0, le=100)
    urbanCenterDistance: float = Field(ge=0, le=10000)
    hasObstacles: bool
    obstacleDescription: str | None = Field(default=None, max_length=500)
    estimatedCost: float = Field(ge=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AnalysisConfigIn(BaseModel):
    slopeWeight: float = Field(ge=0, le=100)
    slopeThreshold: float = Field(ge=0, le=45)
    landUseWeight: float = Field(ge=0, le=100)
    transportWeight: float = Field(ge=0, le=100)
    transportBufferKm: float = Field(ge=0, le=500)
    costWeight: float = Field(ge=0, le=100)
    applyExclusions: bool


@router.post("/assessments")
def create_assessment(payload: AssessmentIn):
    return assessment_service.submit(payload.model_dump())


@router.get("/assessments")
def list_assessments():
    return assessment_service.list_all()


@router.get("/ranking")
def get_ranking():
    """Returns all stored assessments scored and ranked.

    Sprint 2 mock: scoring formula in mesa_service._score(). Real MCDA/AHP
    arrives with EP-13.
    """
    return assessment_service.ranking()


@router.post("/analysis/run")
def run_analysis(config: AnalysisConfigIn):
    weights_sum = (
        config.slopeWeight
        + config.landUseWeight
        + config.transportWeight
        + config.costWeight
    )
    if abs(weights_sum - 100) > 0.01:
        raise HTTPException(status_code=400, detail="Weights must sum to 100")
    job_id = analysis_service.submit(config.model_dump())
    return {"id": job_id}


@router.get("/analysis/status/{job_id}")
def get_analysis_status(job_id: str):
    status = analysis_service.status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return status


@router.get("/export/{format}")
def export_results(format: str):
    """Mock export — returns CSV no matter the requested format until EP-04
    plugs in the real Shapefile/GeoTIFF generation."""
    if format not in {"shapefile", "geotiff", "csv"}:
        raise HTTPException(status_code=400, detail="Unsupported format")

    rows = assessment_service.ranking()
    header = "rank,site_name,total_score,latitude,longitude\n"
    body = "\n".join(
        f'{r["rank"]},"{r["siteName"]}",{r["totalScore"]},{r["latitude"]},{r["longitude"]}'
        for r in rows
    )
    buffer = BytesIO((header + body).encode("utf-8"))
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="ranking.{format}.csv"'},
    )
