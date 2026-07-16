"""Ingest MapBiomas land use/cover per município via GDAL /vsicurl.

Reads the national annual MapBiomas GeoTIFF remotely through ``/vsicurl`` and
clips it to each requested municipal boundary with ``gdalwarp -cutline``
(nearest-neighbour — the band is categorical), so only the município window is
fetched. Land-use reclassification to a suitability score happens at MCDA time
(services/mcda.py), keeping preferences tunable. Registers the COG in
``mesa_a.raster_catalog``.

Env: MAPBIOMAS_LANDUSE_URL (national annual GeoTIFF on GCS), RASTER_DATA_DIR,
GDAL_HTTP_UNSAFESSL. Requires gdal-bin.
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

RASTER_ROOT = os.environ.get("RASTER_DATA_DIR", "/data/raster")
DEFAULT_CODIGOS = ["3550308"]


def _run(cmd: list[str]) -> None:
    logging.info("run: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def process(**kwargs) -> None:
    if not MAPBIOMAS_LANDUSE_URL:
        raise ValueError(
            "MAPBIOMAS_LANDUSE_URL is not set. Configure the collection/year asset URL."
        )
    codigos = (kwargs.get("dag_run").conf or {}).get("codigos_ibge") or DEFAULT_CODIGOS
    src = f"/vsicurl/{MAPBIOMAS_LANDUSE_URL}"
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
        _run(["gdalwarp", "-overwrite", "-t_srs", "EPSG:4674", "-cutline", cutline,
              "-crop_to_cutline", "-r", "near", "-co", "TILED=YES",
              "-co", "COMPRESS=DEFLATE", src, out])
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO mesa_a.raster_catalog (dataset, codigo_ibge, file_path, resolution_m, source_url)
            VALUES ('mapbiomas_landuse', %s, %s, 30.0, %s)
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
    PythonOperator(task_id="clip_per_municipio", python_callable=process)
