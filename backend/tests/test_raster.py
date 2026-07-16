"""Pure tests for the raster helpers (config hash + colorization). No DB/GDAL."""

import numpy as np

from geoavia_backend.services import mcda
from geoavia_backend.services.raster import _colorize, config_hash


def test_config_hash_is_deterministic_and_config_sensitive():
    cfg = {"slopeWeight": 30, "landUseWeight": 25, "slopeThreshold": 2, "applyExclusions": True}
    h1 = config_hash("3550308", cfg)
    h2 = config_hash("3550308", dict(cfg))
    assert h1 == h2  # same inputs → same hash
    assert config_hash("3550308", {**cfg, "slopeWeight": 40}) != h1  # weight change
    assert config_hash("9999999", cfg) != h1  # município change


def test_colorize_transparent_where_excluded_and_opaque_where_valid():
    suit = np.array([[mcda.NODATA, 0.0, 50.0, 100.0]])
    rgba = _colorize(suit, mcda.NODATA)
    assert rgba.shape == (4, 1, 4)  # (bands, H, W)
    alpha = rgba[3, 0, :]
    assert alpha[0] == 0  # excluded → transparent
    assert (alpha[1:] == 180).all()  # valid cells → opaque
    # Ramp endpoints: low suitability is red-ish, high is green-ish.
    assert rgba[0, 0, 1] == 255 and rgba[1, 0, 1] == 0  # score 0 → red
    assert rgba[0, 0, 3] == 0 and rgba[1, 0, 3] == 255  # score 100 → green
