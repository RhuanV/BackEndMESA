"""MESA endpoints consumed by the frontend via apiClient
(frontend/src/features/{assessment,analysis,results}/services)."""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from geoavia_backend.core.auth import obtain_current_user
from geoavia_backend.schemas.mesa import AnalysisConfigIn, AssessmentIn
from geoavia_backend.services.audit import AuditService
from geoavia_backend.services.mesa import AnalysisJobService, AssessmentService

router = APIRouter(dependencies=[Depends(obtain_current_user)])
assessment_service = AssessmentService()
analysis_service = AnalysisJobService()
audit_service = AuditService()


def _client_ip(request: Request) -> str | None:
    """Best-effort client IP for the audit log (no proxy header trust)."""
    return request.client.host if request.client else None


@router.post("/assessments")
def create_assessment(payload: AssessmentIn):
    return assessment_service.submit(payload.model_dump())


@router.get("/assessments")
def list_assessments():
    return assessment_service.list_all()


@router.get("/ranking")
def get_ranking():
    """Returns all stored assessments, scored and ranked."""
    return assessment_service.ranking()


@router.post("/analysis/run")
def run_analysis(
    config: AnalysisConfigIn,
    request: Request,
    current_user: dict = Depends(obtain_current_user),
):
    weights_sum = (
        config.slopeWeight + config.landUseWeight + config.transportWeight + config.costWeight
    )
    if abs(weights_sum - 100) > 0.01:
        raise HTTPException(status_code=400, detail="Weights must sum to 100")
    job_id = analysis_service.submit(config.model_dump())
    audit_service.record(
        action="ANALYSIS_RUN",
        user_id=int(current_user["sub"]) if str(current_user.get("sub", "")).isdigit() else None,
        username=current_user["username"],
        user_role=current_user["role"],
        resource=job_id,
        detail="MCDA analysis submitted",
        ip_address=_client_ip(request),
    )
    return {"id": job_id}


@router.get("/analysis/status/{job_id}")
def get_analysis_status(job_id: str):
    status = analysis_service.status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return status


@router.get("/export/{format}")
def export_results(
    format: str,
    request: Request,
    codigo_ibge: str | None = Query(default=None, max_length=7),
    slope_weight: float = Query(default=30.0, ge=0, le=100),
    land_use_weight: float = Query(default=25.0, ge=0, le=100),
    transport_weight: float = Query(default=25.0, ge=0, le=100),
    cost_weight: float = Query(default=20.0, ge=0, le=100),
    slope_threshold: float = Query(default=2.0, ge=0, le=45),
    apply_exclusions: bool = Query(default=True),
    current_user: dict = Depends(obtain_current_user),
):
    """Exports the current ranking.

    - `shapefile`: zipped Esri Shapefile (.shp/.dbf/.shx/.prj/.cpg), one point
      per assessment in SIRGAS 2000 (EPSG:4674), with scores in the attributes.
    - `csv`: same ranking as CSV.
    - `geotiff`: MCDA suitability raster for `codigo_ibge` (EPSG:4674). Requires
      the ANADEM/MapBiomas rasters for that município to be ingested (409 if not).
    """
    if format not in {"shapefile", "geotiff", "csv"}:
        raise HTTPException(status_code=400, detail="Unsupported format")

    if format == "geotiff":
        if not codigo_ibge:
            raise HTTPException(
                status_code=400,
                detail="codigo_ibge é obrigatório para exportar GeoTIFF de adequabilidade.",
            )
        # Lazy import so the raster stack is only loaded when actually exporting.
        from geoavia_backend.services.raster import RasterDataUnavailable, RasterService

        config = {
            "slopeWeight": slope_weight,
            "landUseWeight": land_use_weight,
            "transportWeight": transport_weight,
            "costWeight": cost_weight,
            "slopeThreshold": slope_threshold,
            "applyExclusions": apply_exclusions,
        }
        try:
            tiff_bytes = RasterService().export_suitability_geotiff(codigo_ibge, config)
        except RasterDataUnavailable as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        sub = str(current_user.get("sub", ""))
        audit_service.record(
            action="EXPORT",
            user_id=int(sub) if sub.isdigit() else None,
            username=current_user["username"],
            user_role=current_user["role"],
            resource=f"geotiff:{codigo_ibge}",
            detail=f"Exported suitability GeoTIFF for {codigo_ibge}",
            ip_address=_client_ip(request),
        )
        return StreamingResponse(
            BytesIO(tiff_bytes),
            media_type="image/tiff",
            headers={
                "Content-Disposition": f'attachment; filename="mesa_suitability_{codigo_ibge}.tif"'
            },
        )

    audit_service.record(
        action="EXPORT",
        user_id=int(current_user["sub"]) if str(current_user.get("sub", "")).isdigit() else None,
        username=current_user["username"],
        user_role=current_user["role"],
        resource=format,
        detail=f"Exported ranking as {format}",
        ip_address=_client_ip(request),
    )

    if format == "shapefile":
        try:
            zip_bytes = assessment_service.export_as_shapefile()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return StreamingResponse(
            BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="mesa_ranking.zip"'},
        )

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
        headers={"Content-Disposition": 'attachment; filename="mesa_ranking.csv"'},
    )
