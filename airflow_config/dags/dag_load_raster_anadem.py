"""Ingest ANADEM MDT (30 m) per município → percent-slope COG, via GDAL /vsicurl.

For each requested município (DAG run conf ``codigos_ibge``) the ANADEM MGRS tile
covering it is read remotely through ``/vsicurl`` and clipped to the municipal
boundary with ``gdalwarp -cutline`` — so only the município window is fetched, no
multi-GB national download. ``gdaldem slope -p`` then derives percent slope. Both
products are registered in ``mesa_a.raster_catalog`` for the backend MCDA.

Env: ANADEM_MDT_URL (tile base URL or a single .tif), RASTER_DATA_DIR,
GDAL_HTTP_UNSAFESSL (set "YES" only as a documented exception for gov TLS).
Requires gdal-bin.
"""
import logging
import os
import subprocess
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
sys.path.insert(0, plugins_dir)

from config_urls import ANADEM_MDT_URL  # noqa: E402

RASTER_ROOT = os.environ.get("RASTER_DATA_DIR", "/data/raster")
DEFAULT_CODIGOS = ["3550308"]  # pilot município (São Paulo/SP)
_BAND_LETTERS = "CDEFGHJKLMNPQRSTUVWX"  # MGRS latitude bands (no I/O)


def _mgrs_zone(lon: float, lat: float) -> str:
    """MGRS grid zone (UTM zone number + latitude band letter), e.g. '22K'."""
    utm_zone = int((lon + 180) // 6) + 1
    band = _BAND_LETTERS[max(0, min(len(_BAND_LETTERS) - 1, int((lat + 80) // 8)))]
    return f"{utm_zone}{band}"


def _tile_url(lon: float, lat: float) -> str:
    """ANADEM tile URL for a point. A configured .tif is used as-is; otherwise
    ANADEM_MDT_URL is treated as a directory base and the MGRS tile is appended."""
    if ANADEM_MDT_URL.endswith(".tif"):
        return ANADEM_MDT_URL
    base = ANADEM_MDT_URL if ANADEM_MDT_URL.endswith("/") else ANADEM_MDT_URL + "/"
    return f"{base}anadem_v1_{_mgrs_zone(lon, lat)}.tif"


def _run(cmd: list[str]) -> None:
    logging.info("run: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def _write_cutline(conn, codigo: str, path: str) -> tuple[bool, float, float]:
    """Writes the municipal boundary GeoJSON cutline; returns (ok, lon, lat)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT ST_AsGeoJSON(geom), ST_X(ST_Centroid(geom)), ST_Y(ST_Centroid(geom)) "
        "FROM mesa_a.vetor_limites_municipais WHERE codigo_ibge = %s;",
        (codigo,),
    )
    row = cur.fetchone()
    cur.close()
    if not row or not row[0]:
        return False, 0.0, 0.0
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            '{"type":"FeatureCollection","features":[{"type":"Feature",'
            '"properties":{},"geometry":' + row[0] + "}]}"
        )
    return True, float(row[1]), float(row[2])


def process(**kwargs) -> None:
    codigos = (kwargs.get("dag_run").conf or {}).get("codigos_ibge") or DEFAULT_CODIGOS
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    for codigo in codigos:
        muni_dir = os.path.join(RASTER_ROOT, codigo)
        os.makedirs(muni_dir, exist_ok=True)
        cutline = os.path.join(muni_dir, "muni.geojson")
        ok, lon, lat = _write_cutline(conn, codigo, cutline)
        if not ok:
            logging.warning("No municipal boundary for %s; skipping.", codigo)
            continue

        src = f"/vsicurl/{_tile_url(lon, lat)}"
        mdt = os.path.join(muni_dir, "anadem_mdt.tif")
        slope = os.path.join(muni_dir, "anadem_slope.tif")
        _run(["gdalwarp", "-overwrite", "-t_srs", "EPSG:4674", "-cutline", cutline,
              "-crop_to_cutline", "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", src, mdt])
        _run(["gdaldem", "slope", "-p", "-s", "111120", "-compute_edges",
              "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", mdt, slope])
        _register(conn, "anadem_mdt", codigo, mdt)
        _register(conn, "anadem_slope", codigo, slope)
    conn.close()


def _register(conn, dataset: str, codigo: str, path: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mesa_a.raster_catalog (dataset, codigo_ibge, file_path, resolution_m, source_url)
        VALUES (%s, %s, %s, 30.0, %s)
        ON CONFLICT (dataset, codigo_ibge) DO UPDATE SET
            file_path = EXCLUDED.file_path, resolution_m = EXCLUDED.resolution_m,
            source_url = EXCLUDED.source_url, generated_at = NOW();
        """,
        (dataset, codigo, path, ANADEM_MDT_URL),
    )
    conn.commit()
    cur.close()
    logging.info("Registered %s for %s at %s", dataset, codigo, path)


with DAG(
    dag_id="load_raster_anadem",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["raster", "anadem", "topografia", "rf03"],
) as dag:
    PythonOperator(task_id="clip_and_slope", python_callable=process)
