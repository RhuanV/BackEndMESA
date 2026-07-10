"""HU-31: ingest an uploaded zipped shapefile (geopandas) into
`mesa_a.user_uploaded_features`, reprojected to SIRGAS 2000 (EPSG:4674).

Accepts a single ZIP with `.shp` + `.dbf` + `.shx`. Without a `.prj` the source
SRID is unknown and the input is assumed to already be in 4674.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import zipfile

import geopandas as gpd
import math
import psycopg2

from geoavia_backend.core.geo_params import normalize_zoom, parse_bbox
from geoavia_backend.core.roles import ADMIN_ROLES
from geoavia_backend.repositories.shapefiles import ShapefilesRepository

# Uploader identity fields exposed only to administrators (audit view).
_UPLOADER_IDENTITY_FIELDS = ("user_id", "username", "user_role")

TARGET_SRID = 4674  # SIRGAS 2000
MAX_FEATURES_PER_UPLOAD = 50_000

logger = logging.getLogger(__name__)


class ShapefileError(Exception):
    """Raised when the uploaded archive cannot be processed."""


class ShapefilesService:
    def __init__(self) -> None:
        self.repo = ShapefilesRepository()

    def import_zip(
        self,
        layer_name: str,
        description: str | None,
        original_filename: str | None,
        zip_bytes: bytes,
        user_id: int | None,
        username: str,
        user_role: str,
    ) -> dict:
        """End-to-end: validate ZIP → read .shp → reproject → persist."""
        with tempfile.TemporaryDirectory() as work_dir:
            shp_path = self._extract_shapefile(zip_bytes, work_dir)
            gdf, source_srid = self._read_and_reproject(shp_path)

            if len(gdf) > MAX_FEATURES_PER_UPLOAD:
                raise ShapefileError(
                    f"Too many features ({len(gdf)}). Limit is {MAX_FEATURES_PER_UPLOAD}."
                )

            try:
                upload_id = self.repo.create_layer(
                    layer_name=layer_name,
                    description=description,
                    user_id=user_id,
                    username=username,
                    user_role=user_role,
                    original_filename=original_filename,
                    source_srid=source_srid,
                )
                features = self._to_feature_rows(gdf)
                inserted = self.repo.insert_features(upload_id, features)
            except psycopg2.Error as exc:
                logger.exception("DB error persisting shapefile upload")
                raise ShapefileError(
                    f"Failed to save to the database: {exc.pgcode or 'unknown error'}"
                ) from exc

            return {
                "upload_id": upload_id,
                "layer_name": layer_name,
                "feature_count": inserted,
                "source_srid": source_srid,
                "target_srid": TARGET_SRID,
            }

    def list_layers(self, limit: int = 100, viewer_role: str | None = None) -> list[dict]:
        """Lists uploads. Uploader identity (user_id/username/user_role) is only
        included for administrators; other roles get a redacted, need-to-know view."""
        layers = self.repo.list_layers(limit=limit)
        if viewer_role in ADMIN_ROLES:
            return layers
        return [
            {k: v for k, v in layer.items() if k not in _UPLOADER_IDENTITY_FIELDS}
            for layer in layers
        ]

    def fetch_features(
        self,
        upload_id: int,
        zoom: str | None = None,
        bbox_raw: str | None = None,
    ) -> dict:
        if not self.repo.layer_exists(upload_id):
            raise ShapefileError(f"Upload not found: {upload_id}")
        zoom = normalize_zoom(zoom)
        bbox = parse_bbox(bbox_raw) if bbox_raw else None
        return self.repo.fetch_features_as_geojson(upload_id, zoom=zoom, bbox=bbox)

    @staticmethod
    def _extract_shapefile(zip_bytes: bytes, work_dir: str) -> str:
        zip_path = os.path.join(work_dir, "upload.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(work_dir)
        except zipfile.BadZipFile as exc:
            raise ShapefileError("Uploaded file is not a valid ZIP archive.") from exc

        shp_files: list[str] = []
        for root, _, files in os.walk(work_dir):
            for f in files:
                if f.lower().endswith(".shp"):
                    shp_files.append(os.path.join(root, f))

        if not shp_files:
            raise ShapefileError("No .shp file found inside the ZIP.")
        if len(shp_files) > 1:
            raise ShapefileError(
                f"Multiple .shp files found ({len(shp_files)}). Upload one shapefile at a time."
            )

        shp_path = shp_files[0]
        base = os.path.splitext(shp_path)[0]
        for required_ext in (".dbf", ".shx"):
            if not os.path.exists(base + required_ext):
                raise ShapefileError(
                    f"Shapefile is missing required companion file: {required_ext}"
                )
        return shp_path

    @staticmethod
    def _read_and_reproject(shp_path: str) -> tuple[gpd.GeoDataFrame, int | None]:
        try:
            gdf = gpd.read_file(shp_path)
        except Exception as exc:
            raise ShapefileError(f"Failed to read shapefile: {exc}") from exc

        if gdf.empty:
            raise ShapefileError("Shapefile contains no features.")

        source_srid: int | None = None
        if gdf.crs is None:
            logger.warning(
                "Shapefile has no .prj — assuming source CRS is already SIRGAS 2000 (4674)."
            )
            gdf = gdf.set_crs(epsg=TARGET_SRID)
        else:
            try:
                source_srid = gdf.crs.to_epsg()
            except Exception:
                source_srid = None
            if source_srid != TARGET_SRID:
                gdf = gdf.to_crs(epsg=TARGET_SRID)

        return gdf, source_srid

    @staticmethod
    def _safe_json_value(value):
        """Convert NaN/Inf floats (including numpy.float64 scalars) to None.

        json.dumps(float('nan')) produces the bare token `NaN` which is not
        valid JSON. PostgreSQL's ::jsonb cast rejects it with error 22P02
        (invalid_text_representation). Converting to None serialises as null.
        """
        try:
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return None
        except (TypeError, ValueError):
            pass
        return value

    @staticmethod
    def _to_feature_rows(gdf: gpd.GeoDataFrame) -> list[tuple[str, str]]:
        """Builds (properties_json, geom_wkt) tuples for bulk insert.

        Properties exclude the geometry column and convert any non-JSON-safe
        values (Timestamps, numpy scalars, NaN/Inf) to safe equivalents.
        NaN/Inf floats become null; other non-serialisable types become strings.
        """
        rows: list[tuple[str, str]] = []
        geom_col = gdf.geometry.name
        for _, row in gdf.iterrows():
            geom = row[geom_col]
            if geom is None or geom.is_empty:
                continue
            props: dict = {}
            for col in gdf.columns:
                if col == geom_col:
                    continue
                value = ShapefilesService._safe_json_value(row[col])
                try:
                    json.dumps(value)
                    props[col] = value
                except (TypeError, ValueError):
                    props[col] = str(row[col]) if row[col] is not None else None

            # allow_nan=False causes ValueError if any NaN slipped through,
            # falling back to stringify everything as a last resort.
            try:
                props_json = json.dumps(props, default=str, allow_nan=False)
            except ValueError:
                props_json = json.dumps({k: str(v) for k, v in props.items()})

            rows.append((props_json, geom.wkt))
        return rows
