"""Safety of the shapefile ZIP extraction (path traversal + size cap)."""
import io
import os
import zipfile

import pytest

from geoavia_backend.services import shapefiles as sf
from geoavia_backend.services.shapefiles import ShapefileError, ShapefilesService


def _zip_bytes(members: dict[str, bytes]) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def test_extracts_only_shapefile_members(tmp_path):
    zf = _zip_bytes({"layer.shp": b"x", "layer.dbf": b"y", "notes.txt": b"z"})
    ShapefilesService._safe_extract(zf, str(tmp_path))
    names = set(os.listdir(tmp_path))
    assert names == {"layer.shp", "layer.dbf"}  # .txt skipped


def test_neutralizes_path_traversal(tmp_path):
    # A member trying to escape (Zip Slip) is flattened into the work dir, never
    # written outside it.
    outside = tmp_path.parent / "evil.shp"
    if outside.exists():
        outside.unlink()
    zf = _zip_bytes({"../evil.shp": b"x", "layer.shp": b"y"})
    ShapefilesService._safe_extract(zf, str(tmp_path))
    assert (tmp_path / "evil.shp").exists()  # contained inside the work dir
    assert not outside.exists()              # never escaped the work dir


def test_enforces_uncompressed_size_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(sf, "MAX_UNCOMPRESSED_BYTES", 1)
    zf = _zip_bytes({"layer.shp": b"way more than one byte"})
    with pytest.raises(ShapefileError):
        ShapefilesService._safe_extract(zf, str(tmp_path))
