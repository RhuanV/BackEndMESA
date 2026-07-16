"""Pure NumPy tests for the MCDA suitability core (no rasterio/DB)."""

import numpy as np

from geoavia_backend.services import mcda


def test_slope_score_flat_is_100_and_steep_is_0():
    slope = np.array([[0.0, 1.0, 2.0, 4.0]])
    scores = mcda.slope_score(slope, max_slope=2.0)
    assert scores[0, 0] == 100.0  # flat
    assert scores[0, 2] == 0.0  # at max_slope
    assert scores[0, 3] == 0.0  # above max_slope clamps to 0
    assert 0.0 < scores[0, 1] < 100.0


def test_reclassify_landuse_maps_codes_and_default():
    landuse = np.array([[15, 24, 999]])  # pasture, urban, unknown
    scores = mcda.reclassify_landuse(landuse)
    assert scores[0, 0] == mcda.LANDUSE_SUITABILITY[15]
    assert scores[0, 1] == mcda.LANDUSE_SUITABILITY[24]
    assert scores[0, 2] == mcda.LANDUSE_DEFAULT


def test_normalize_weights_sums_to_one():
    norm = mcda.normalize_weights({"a": 30, "b": 10, "c": 0})
    assert abs(sum(norm.values()) - 1.0) < 1e-9
    assert norm["a"] == 0.75


def test_normalize_all_zero_is_uniform():
    norm = mcda.normalize_weights({"a": 0, "b": 0})
    assert norm == {"a": 0.5, "b": 0.5}


def test_weighted_suitability_combines_active_criteria():
    scores = {
        "slope": np.array([[100.0, 0.0]]),
        "land_use": np.array([[0.0, 100.0]]),
    }
    # transport/cost absent from scores -> ignored; slope/land_use renormalized 50/50.
    result = mcda.weighted_suitability(
        scores, {"slope": 50, "land_use": 50, "transport": 25, "cost": 25}
    )
    assert result[0, 0] == 50.0
    assert result[0, 1] == 50.0


def test_apply_exclusion_sets_nodata():
    suit = np.array([[80.0, 90.0]])
    mask = np.array([[True, False]])
    out = mcda.apply_exclusion(suit, mask)
    assert out[0, 0] == mcda.NODATA
    assert out[0, 1] == 90.0
