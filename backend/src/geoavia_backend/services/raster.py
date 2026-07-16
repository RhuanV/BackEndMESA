"""Raster IO + MCDA orchestration (Fase 5).

Reads the municipal slope/land-use COGs registered in ``mesa_a.raster_catalog``,
computes the MCDA suitability with the pure NumPy core in ``services.mcda`` and a
real eliminatório mask rasterized from the vector exclusion layers
(``repositories.exclusion``), then:

- writes the suitability COG and registers it in the catalog,
- persists the ranked candidate points to ``mesa_a.suitability_results``,
- exports the suitability GeoTIFF, and
- renders a colorized PNG (+ bounds) for the web-map overlay.

rasterio/NumPy are imported lazily inside methods so the backend still starts if
the raster stack is unavailable; callers map :class:`RasterDataUnavailable` to
HTTP 409. The pure math lives in ``services.mcda`` and is unit-tested there.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from geoavia_backend.repositories.exclusion import ExclusionRepository
from geoavia_backend.repositories.raster import (
    RasterCatalogRepository,
    SuitabilityResultsRepository,
)
from geoavia_backend.services import mcda

RASTER_ROOT = os.environ.get("RASTER_DATA_DIR", "/data/raster")
# How many top-suitability points to persist/rank per run.
TOP_N = 10


class RasterDataUnavailable(Exception):
    """Raised when the municipal rasters needed for MCDA are not ingested yet."""


def config_hash(codigo_ibge: str, config: dict) -> str:
    """Stable hash of the inputs that affect the result (for caching/keys)."""
    keys = (
        "slopeWeight",
        "landUseWeight",
        "transportWeight",
        "costWeight",
        "slopeThreshold",
        "applyExclusions",
    )
    parts = [codigo_ibge] + [f"{k}={config.get(k)}" for k in keys]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


class RasterService:
    def __init__(
        self,
        catalog: RasterCatalogRepository | None = None,
        results: SuitabilityResultsRepository | None = None,
        exclusion: ExclusionRepository | None = None,
    ) -> None:
        self.catalog = catalog or RasterCatalogRepository()
        self.results = results or SuitabilityResultsRepository()
        self.exclusion = exclusion or ExclusionRepository()

    # --- public API -------------------------------------------------------
    def compute_suitability(
        self, codigo_ibge: str, config: dict, case_id: int | None = None
    ) -> dict:
        """Computes + persists the suitability raster and ranked points.

        Returns {file_path, bounds, config_hash, ranked}. Raises
        :class:`RasterDataUnavailable` if the input rasters are not ingested.
        """
        # Catalog check first (no heavy import) so the 409 path works even where
        # rasterio/GDAL are unavailable.
        if not self.catalog.get("anadem_slope", codigo_ibge) or not self.catalog.get(
            "mapbiomas_landuse", codigo_ibge
        ):
            raise RasterDataUnavailable(
                f"Rasters de declividade/uso do solo não ingeridos para o município "
                f"{codigo_ibge}. Rode load_raster_anadem e load_raster_mapbiomas "
                f"(ou use o seed demo)."
            )

        import numpy as np  # noqa: PLC0415
        import rasterio  # noqa: PLC0415
        from rasterio.transform import array_bounds, xy  # noqa: PLC0415

        # Cache (RNF02): if the suitability COG for this exact config already
        # exists, reuse it instead of recomputing (the PNG/GeoTIFF endpoints call
        # this with the same config the job used).
        chash = config_hash(codigo_ibge, config)
        cached = Path(RASTER_ROOT) / codigo_ibge / f"suitability_{chash}.tif"
        if cached.exists():
            with rasterio.open(cached) as src:
                bounds = list(array_bounds(src.height, src.width, src.transform))
            return {
                "file_path": str(cached),
                "bounds": bounds,
                "config_hash": chash,
                "ranked": self.results.list_for(codigo_ibge, chash),
            }

        slope, landuse, profile, transform = self._read_aligned_inputs(codigo_ibge)

        scores = {
            "slope": mcda.slope_score(slope, config.get("slopeThreshold", 2.0) or 2.0),
            "land_use": mcda.reclassify_landuse(landuse.astype("int32")),
        }
        weights = {
            "slope": config.get("slopeWeight", 0.0),
            "land_use": config.get("landUseWeight", 0.0),
            "transport": config.get("transportWeight", 0.0),
            "cost": config.get("costWeight", 0.0),
        }
        suitability = mcda.weighted_suitability(scores, weights)

        # Baseline invalidity: nodata input cells are not evaluable.
        exclusion_mask = ~np.isfinite(slope)
        nodata_slope = profile.get("nodata")
        if nodata_slope is not None:
            exclusion_mask = exclusion_mask | (slope == nodata_slope)
        if config.get("applyExclusions", True):
            exclusion_mask = exclusion_mask | self._exclusion_mask(
                codigo_ibge, suitability.shape, transform
            )
        suitability = mcda.apply_exclusion(suitability, exclusion_mask)

        out_path = self._write_cog(codigo_ibge, config, suitability, profile)
        rows_n, cols_n = suitability.shape
        bounds = list(array_bounds(rows_n, cols_n, transform))
        ranked = self._rank_points(suitability, scores, transform, xy)
        self.results.replace_for(codigo_ibge, config_hash(codigo_ibge, config), case_id, ranked)
        return {
            "file_path": str(out_path),
            "bounds": bounds,
            "config_hash": config_hash(codigo_ibge, config),
            "ranked": ranked,
        }

    def export_suitability_geotiff(self, codigo_ibge: str, config: dict) -> bytes:
        """Returns the suitability GeoTIFF bytes (computing it if needed)."""
        result = self.compute_suitability(codigo_ibge, config)
        return Path(result["file_path"]).read_bytes()

    def render_suitability_png(self, codigo_ibge: str, config: dict) -> tuple[bytes, list[float]]:
        """Returns (PNG bytes, [minx,miny,maxx,maxy]) for the map overlay."""
        import numpy as np  # noqa: PLC0415
        import rasterio  # noqa: PLC0415
        from rasterio.io import MemoryFile  # noqa: PLC0415

        result = self.compute_suitability(codigo_ibge, config)
        with rasterio.open(result["file_path"]) as src:
            suit = src.read(1)
        rgba = _colorize(np.asarray(suit), mcda.NODATA)
        height, width = suit.shape
        with MemoryFile() as mem:
            with mem.open(driver="PNG", width=width, height=height, count=4, dtype="uint8") as dst:
                dst.write(rgba)
            return mem.read(), result["bounds"]

    # --- internals --------------------------------------------------------
    def _read_aligned_inputs(self, codigo_ibge: str):
        import numpy as np  # noqa: PLC0415
        import rasterio  # noqa: PLC0415
        from rasterio.warp import Resampling, reproject  # noqa: PLC0415

        slope_entry = self.catalog.get("anadem_slope", codigo_ibge)
        landuse_entry = self.catalog.get("mapbiomas_landuse", codigo_ibge)
        with rasterio.open(slope_entry["file_path"]) as slope_src:
            slope = slope_src.read(1).astype("float64")
            profile = slope_src.profile
            transform = slope_src.transform
            with rasterio.open(landuse_entry["file_path"]) as lu_src:
                landuse = np.zeros(slope.shape, dtype="float32")
                reproject(
                    source=rasterio.band(lu_src, 1),
                    destination=landuse,
                    src_transform=lu_src.transform,
                    src_crs=lu_src.crs,
                    dst_transform=transform,
                    dst_crs=slope_src.crs,
                    resampling=Resampling.nearest,
                )
        return slope, landuse, profile, transform

    def _exclusion_mask(self, codigo_ibge: str, shape, transform):
        """Boolean mask — True where a cell is excluded (outside the município or
        inside a restrictive/exclusion geometry)."""
        import numpy as np  # noqa: PLC0415
        from rasterio.features import rasterize  # noqa: PLC0415

        muni = self.exclusion.municipality(codigo_ibge)
        if not muni:
            return np.zeros(shape, dtype=bool)

        inside = rasterize(
            [(muni["geojson"], 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8"
        )
        excluded = np.zeros(shape, dtype="uint8")
        geoms = self.exclusion.exclusion_geometries(codigo_ibge)
        if geoms:
            excluded = rasterize(
                [(g, 1) for g in geoms],
                out_shape=shape,
                transform=transform,
                fill=0,
                dtype="uint8",
                all_touched=True,
            )
        return (inside == 0) | (excluded == 1)

    def _write_cog(self, codigo_ibge: str, config: dict, suitability, profile) -> Path:
        import rasterio  # noqa: PLC0415

        out_dir = Path(RASTER_ROOT) / codigo_ibge
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"suitability_{config_hash(codigo_ibge, config)}.tif"
        out_profile = dict(profile)
        out_profile.update(
            dtype="float32", count=1, nodata=mcda.NODATA, compress="deflate", tiled=True
        )
        with rasterio.open(out_path, "w", **out_profile) as dst:
            dst.write(suitability.astype("float32"), 1)
        self.catalog.upsert(
            dataset="suitability",
            codigo_ibge=codigo_ibge,
            file_path=str(out_path),
            resolution_m=None,
            nodata=mcda.NODATA,
            source_url=None,
        )
        return out_path

    def _rank_points(self, suitability, scores, transform, xy) -> list[dict]:
        import numpy as np  # noqa: PLC0415

        valid = suitability > mcda.NODATA
        if not valid.any():
            return []
        flat = np.where(valid, suitability, -np.inf).ravel()
        n = min(TOP_N, int(valid.sum()))
        top_idx = np.argpartition(flat, -n)[-n:]
        top_idx = top_idx[np.argsort(flat[top_idx])[::-1]]
        rows = []
        for rank, flat_i in enumerate(top_idx, start=1):
            row, col = divmod(int(flat_i), suitability.shape[1])
            lon, lat = xy(transform, row, col)
            rows.append(
                {
                    "rank": rank,
                    "total_score": round(float(suitability[row, col]), 2),
                    "slope_score": round(float(scores["slope"][row, col]), 2),
                    "land_use_score": round(float(scores["land_use"][row, col]), 2),
                    "transport_score": None,
                    "cost_score": None,
                    "latitude": round(float(lat), 6),
                    "longitude": round(float(lon), 6),
                }
            )
        return rows


def _colorize(suit, nodata: float):
    """Maps a 0–100 suitability array (H,W) to an RGBA uint8 image (4,H,W).

    Red (low) → yellow → green (high); excluded/nodata cells are transparent.
    """
    import numpy as np  # noqa: PLC0415

    valid = suit > nodata
    t = np.clip(np.where(valid, suit, 0.0) / 100.0, 0.0, 1.0)
    red = np.where(t < 0.5, 255, np.round(255 * (1 - (t - 0.5) * 2))).astype("uint8")
    green = np.where(t < 0.5, np.round(255 * (t * 2)), 255).astype("uint8")
    blue = np.zeros_like(red, dtype="uint8")
    alpha = np.where(valid, 180, 0).astype("uint8")
    return np.stack([red, green, blue, alpha], axis=0)
