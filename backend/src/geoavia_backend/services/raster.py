"""Raster IO + MCDA orchestration for GeoTIFF export (Fase 5).

Reads the pre-clipped municipal COGs registered in ``mesa_a.raster_catalog``
(ANADEM slope + MapBiomas land use), computes the MCDA suitability with the pure
numeric core in ``services.mcda`` and returns a GeoTIFF.

rasterio/GDAL are imported lazily inside the methods so the backend still starts
(and the rest of the API works) even if the raster stack is unavailable; callers
translate :class:`RasterDataUnavailable` into an HTTP 409.
"""

from __future__ import annotations

from geoavia_backend.repositories.raster import RasterCatalogRepository
from geoavia_backend.services import mcda


class RasterDataUnavailable(Exception):
    """Raised when the municipal rasters needed for MCDA are not ingested yet."""


class RasterService:
    def __init__(self, repo: RasterCatalogRepository | None = None) -> None:
        self.repo = repo or RasterCatalogRepository()

    def export_suitability_geotiff(self, codigo_ibge: str, config: dict) -> bytes:
        """Computes the suitability raster for a município and returns GeoTIFF bytes.

        Requires the ``anadem_slope`` and ``mapbiomas_landuse`` products for the
        município to have been ingested (Airflow raster DAGs). Raises
        :class:`RasterDataUnavailable` otherwise.
        """
        # Check the catalog first (no heavy imports) so the "not ingested yet"
        # path (→ HTTP 409) works even where rasterio/GDAL are unavailable.
        slope_entry = self.repo.get("anadem_slope", codigo_ibge)
        landuse_entry = self.repo.get("mapbiomas_landuse", codigo_ibge)
        if not slope_entry or not landuse_entry:
            raise RasterDataUnavailable(
                f"Rasters de declividade/uso do solo ainda não ingeridos para o "
                f"município {codigo_ibge}. Rode as DAGs load_raster_anadem e "
                f"load_raster_mapbiomas primeiro."
            )

        import numpy as np  # noqa: PLC0415 — lazy, heavy import
        import rasterio  # noqa: PLC0415
        from rasterio.io import MemoryFile  # noqa: PLC0415
        from rasterio.warp import Resampling, reproject  # noqa: PLC0415

        with rasterio.open(slope_entry["file_path"]) as slope_src:
            slope = slope_src.read(1).astype("float64")
            profile = slope_src.profile
            dst_transform = slope_src.transform
            dst_crs = slope_src.crs
            height, width = slope.shape

            # Resample land use onto the slope grid (categorical → nearest).
            with rasterio.open(landuse_entry["file_path"]) as lu_src:
                landuse = np.zeros((height, width), dtype="float32")
                reproject(
                    source=rasterio.band(lu_src, 1),
                    destination=landuse,
                    src_transform=lu_src.transform,
                    src_crs=lu_src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                )

        weights = {
            "slope": config.get("slopeWeight", 0.0),
            "land_use": config.get("landUseWeight", 0.0),
            "transport": config.get("transportWeight", 0.0),
            "cost": config.get("costWeight", 0.0),
        }
        scores = {
            "slope": mcda.slope_score(slope, config.get("slopeThreshold", 2.0) or 2.0),
            "land_use": mcda.reclassify_landuse(landuse.astype("int32")),
        }
        suitability = mcda.weighted_suitability(scores, weights)

        # Eliminatório (proxy): when exclusions are on, drop cells above the slope
        # threshold. Full vector-based exclusion (Terras Indígenas/UCs/buffers) is
        # rasterized on the server in a follow-up; this keeps the export usable.
        if config.get("applyExclusions", True):
            exclusion = slope > (config.get("slopeThreshold", 2.0) or 2.0)
            suitability = mcda.apply_exclusion(suitability, exclusion)

        profile.update(dtype="float32", count=1, nodata=mcda.NODATA, compress="deflate")
        with MemoryFile() as memfile:
            with memfile.open(**profile) as dst:
                dst.write(suitability.astype("float32"), 1)
            return memfile.read()
