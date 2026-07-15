"""MCDA suitability — pure numeric core (RF05).

This module holds the per-cell multi-criteria computation as plain NumPy so it
is fully unit-testable without rasterio, GDAL or a database. The raster IO
(reading the municipal COGs, rasterizing the exclusion mask, writing the output
GeoTIFF) lives in ``services.raster`` and calls these functions.

Convention: every criterion sub-score and the final suitability are on a 0–100
scale; excluded cells carry ``NODATA``.
"""

from __future__ import annotations

import numpy as np

# Sentinel for cells removed by the eliminatório (exclusion) mask.
NODATA = -1.0

# MapBiomas (Coleção Brasil) class code → suitability preference (0–100).
# Flat, already-anthropized land (pasture/agriculture) is preferred for an
# airport; forest, water, wetlands and urban areas are penalized. Codes not
# listed fall back to LANDUSE_DEFAULT.
LANDUSE_SUITABILITY: dict[int, float] = {
    3: 20.0,  # Forest formation
    4: 40.0,  # Savanna formation
    5: 20.0,  # Mangrove
    11: 10.0,  # Wetland
    12: 70.0,  # Grassland
    15: 90.0,  # Pasture
    18: 80.0,  # Agriculture
    19: 80.0,  # Temporary crops
    20: 80.0,  # Sugar cane
    21: 75.0,  # Mosaic of uses
    24: 5.0,  # Urban area
    25: 30.0,  # Other non-vegetated
    30: 10.0,  # Mining
    33: 0.0,  # Water
}
LANDUSE_DEFAULT = 50.0


def slope_score(slope: np.ndarray, max_slope: float) -> np.ndarray:
    """0–100 score from percent slope: 100 on flat ground, 0 at/above max_slope.

    ``max_slope`` is the slope (percent) at which a site becomes unsuitable on
    the slope criterion; MESA marks steep terrain as critical.
    """
    max_slope = max(float(max_slope), 1e-6)
    score = 100.0 * (1.0 - np.asarray(slope, dtype="float64") / max_slope)
    return np.clip(score, 0.0, 100.0)


def reclassify_landuse(
    landuse: np.ndarray,
    lut: dict[int, float] | None = None,
    default: float = LANDUSE_DEFAULT,
) -> np.ndarray:
    """Maps integer land-use class codes to a 0–100 suitability array."""
    lut = lut or LANDUSE_SUITABILITY
    codes = np.asarray(landuse)
    out = np.full(codes.shape, float(default), dtype="float64")
    for code, value in lut.items():
        out[codes == code] = value
    return out


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Normalizes criterion weights so they sum to 1 (all-zero → uniform)."""
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        n = len(weights) or 1
        return {k: 1.0 / n for k in weights}
    return {k: max(0.0, float(v)) / total for k, v in weights.items()}


def weighted_suitability(
    scores: dict[str, np.ndarray],
    weights: dict[str, float],
) -> np.ndarray:
    """Weighted sum of per-criterion 0–100 arrays → a 0–100 suitability array.

    Only criteria present in ``scores`` are combined; their weights are
    renormalized so they always sum to 1.
    """
    active = {k: w for k, w in weights.items() if k in scores}
    norm = normalize_weights(active)
    shape = next(iter(scores.values())).shape
    total = np.zeros(shape, dtype="float64")
    for key, arr in scores.items():
        total += np.asarray(arr, dtype="float64") * norm.get(key, 0.0)
    return np.clip(total, 0.0, 100.0)


def apply_exclusion(
    suitability: np.ndarray,
    exclusion_mask: np.ndarray,
    nodata: float = NODATA,
) -> np.ndarray:
    """Sets excluded cells (mask True) to ``nodata`` — the eliminatório step."""
    out = np.array(suitability, dtype="float64", copy=True)
    out[np.asarray(exclusion_mask, dtype=bool)] = nodata
    return out
