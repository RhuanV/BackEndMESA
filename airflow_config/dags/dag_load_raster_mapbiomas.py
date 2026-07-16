"""Ingest MapBiomas land use/cover (10 m), clip per município, register COGs.

Pattern mirrors the ANADEM DAG: download the annual land-use GeoTIFF once,
reproject to SIRGAS 2000 (nearest-neighbour — the band is categorical), then
clip to each requested municipal boundary and register the COG in
``mesa_a.raster_catalog``. Land-use reclassification to a suitability score
happens at MCDA time (services/mcda.py), keeping preferences tunable.

Set MAPBIOMAS_LANDUSE_URL in the environment to the concrete collection/year
asset before running. Requires gdal-bin.
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

from config_urls import MAPBIOMAS_LANDUSE_URL  # noqa: E402
from secure_http import government_get  # noqa: E402

RASTER_ROOT = os.environ.get("RASTER_DATA_DIR", "/data/raster")
DEFAULT_CODIGOS = ["3550308"]


def _run(cmd: list[str]) -> None:
    logging.info("run: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def extract_landuse(**kwargs) -> str:
    if not MAPBIOMAS_LANDUSE_URL:
        raise ValueError(
            "MAPBIOMAS_LANDUSE_URL is not set. Configure the collection/year asset "
            "URL in the environment before running this DAG."
        )
    os.makedirs(RASTER_ROOT, exist_ok=True)
    raw = os.path.join(RASTER_ROOT, "mapbiomas_raw.tif")
    if not os.path.exists(raw):
        logging.info("Downloading MapBiomas land use from %s", MAPBIOMAS_LANDUSE_URL)
        resp = government_get(MAPBIOMAS_LANDUSE_URL, stream=True)
        resp.raise_for_status()
        with open(raw, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    reproj = os.path.join(RASTER_ROOT, "mapbiomas_landuse_4674.tif")
    _run(["gdalwarp", "-overwrite", "-t_srs", "EPSG:4674", "-r", "near", raw, reproj])
    return reproj


def clip_per_municipio(**kwargs) -> None:
    ti = kwargs["ti"]
    src = ti.xcom_pull(task_ids="extract_landuse")
    codigos = (kwargs.get("dag_run").conf or {}).get("codigos_ibge") or DEFAULT_CODIGOS

    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    for codigo in codigos:
        muni_dir = os.path.join(RASTER_ROOT, codigo)
        os.makedirs(muni_dir, exist_ok=True)
        cutline = os.path.join(muni_dir, "muni.geojson")
        if not os.path.exists(cutline):
            cur = conn.cursor()
            cur.execute(
                "SELECT ST_AsGeoJSON(geom) FROM mesa_a.vetor_limites_municipais "
                "WHERE codigo_ibge = %s;",
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

        out = os.path.join(muni_dir, "mapbiomas_landuse.tif")
        _run(
            [
                "gdalwarp", "-overwrite", "-cutline", cutline, "-crop_to_cutline",
                "-r", "near", "-co", "TILED=YES", "-co", "COMPRESS=DEFLATE", src, out,
            ]
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO mesa_a.raster_catalog (dataset, codigo_ibge, file_path, resolution_m, source_url)
            VALUES ('mapbiomas_landuse', %s, %s, 10.0, %s)
            ON CONFLICT (dataset, codigo_ibge) DO UPDATE SET
                file_path = EXCLUDED.file_path, resolution_m = EXCLUDED.resolution_m,
                source_url = EXCLUDED.source_url, generated_at = NOW();
            """,
            (codigo, out, MAPBIOMAS_LANDUSE_URL),
        )
        conn.commit()
        cur.close()
        logging.info("Registered mapbiomas_landuse for %s at %s", codigo, out)
    conn.close()


with DAG(
    dag_id="load_raster_mapbiomas",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["raster", "mapbiomas", "uso-do-solo", "rf03"],
) as dag:
    extract_task = PythonOperator(task_id="extract_landuse", python_callable=extract_landuse)
    clip_task = PythonOperator(task_id="clip_per_municipio", python_callable=clip_per_municipio)
    extract_task >> clip_task
