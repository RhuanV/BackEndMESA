"""Ingest ANADEM MDT (30 m), derive percent-slope per município, register COGs.

Pattern: download the MDT once, reproject to SIRGAS 2000 (EPSG:4674), then for
each requested município (DAG run conf ``codigos_ibge``) clip to the municipal
boundary and run ``gdaldem slope`` to produce a per-municipal slope COG. The MDT
and slope products are registered in ``mesa_a.raster_catalog`` for the backend
MCDA/GeoTIFF export (Fase 5). Pre-clipping is the key RNF02 lever.

Requires gdal-bin (gdalwarp/gdaldem) — installed in the Airflow image.
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
from secure_http import government_get  # noqa: E402

RASTER_ROOT = os.environ.get("RASTER_DATA_DIR", "/data/raster")
DEFAULT_CODIGOS = ["3550308"]  # São Paulo (SP) as the pilot município.


def _run(cmd: list[str]) -> None:
    logging.info("run: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def extract_mdt(**kwargs) -> str:
    os.makedirs(RASTER_ROOT, exist_ok=True)
    raw = os.path.join(RASTER_ROOT, "anadem_raw.tif")
    if not os.path.exists(raw):
        logging.info("Downloading ANADEM MDT from %s", ANADEM_MDT_URL)
        resp = government_get(ANADEM_MDT_URL, stream=True)
        resp.raise_for_status()
        with open(raw, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    # Ensure SIRGAS 2000 for consistency with the vector stack.
    reproj = os.path.join(RASTER_ROOT, "anadem_mdt_4674.tif")
    _run(["gdalwarp", "-overwrite", "-t_srs", "EPSG:4674", raw, reproj])
    return reproj


def clip_and_slope(**kwargs) -> None:
    ti = kwargs["ti"]
    mdt = ti.xcom_pull(task_ids="extract_mdt")
    codigos = (kwargs.get("dag_run").conf or {}).get("codigos_ibge") or DEFAULT_CODIGOS

    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()

    for codigo in codigos:
        muni_dir = os.path.join(RASTER_ROOT, codigo)
        os.makedirs(muni_dir, exist_ok=True)
        cutline = os.path.join(muni_dir, "muni.geojson")

        # Export the municipal boundary as a GeoJSON cutline.
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ST_AsGeoJSON(geom) FROM mesa_a.vetor_limites_municipais
             WHERE codigo_ibge = %s;
            """,
            (codigo,),
        )
        row = cur.fetchone()
        cur.close()
        if not row or not row[0]:
            logging.warning("No municipal boundary for %s; skipping.", codigo)
            continue
        with open(cutline, "w", encoding="utf-8") as f:
            f.write(
                '{"type":"FeatureCollection","features":[{"type":"Feature",'
                '"properties":{},"geometry":' + row[0] + "}]}"
            )

        mdt_clip = os.path.join(muni_dir, "anadem_mdt.tif")
        slope_tif = os.path.join(muni_dir, "anadem_slope.tif")
        _run(
            [
                "gdalwarp", "-overwrite", "-cutline", cutline, "-crop_to_cutline",
                "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", mdt, mdt_clip,
            ]
        )
        # Percent slope; -s 111120 accounts for a degree-based (EPSG:4674) DEM.
        _run(
            [
                "gdaldem", "slope", "-p", "-s", "111120", "-compute_edges",
                "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", mdt_clip, slope_tif,
            ]
        )
        _register(conn, "anadem_mdt", codigo, mdt_clip, 30.0)
        _register(conn, "anadem_slope", codigo, slope_tif, 30.0)

    conn.close()


def _register(conn, dataset: str, codigo: str, path: str, resolution: float) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mesa_a.raster_catalog (dataset, codigo_ibge, file_path, resolution_m, source_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (dataset, codigo_ibge) DO UPDATE SET
            file_path = EXCLUDED.file_path, resolution_m = EXCLUDED.resolution_m,
            source_url = EXCLUDED.source_url, generated_at = NOW();
        """,
        (dataset, codigo, path, resolution, ANADEM_MDT_URL),
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
    extract_task = PythonOperator(task_id="extract_mdt", python_callable=extract_mdt)
    slope_task = PythonOperator(task_id="clip_and_slope", python_callable=clip_and_slope)
    extract_task >> slope_task
