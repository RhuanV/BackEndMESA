"""Transmission lines DAG (ANEEL/SIGEL, ArcGIS REST API).

Downloads, processes with GeoPandas and loads into mesa_a.vetor_gov_linhas_transmissao.
"""
import os
import logging
import requests
import json
import shutil
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import geopandas as gpd
from psycopg2.extras import execute_batch

import sys
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)
from config_urls import LINHAS_TRANSMISSAO_GOV_URL
from secure_http import government_get

def extract_linhas_transmissao(**kwargs) -> str:
    """Extract: downloads transmission lines from the SIGEL API as GeoJSON,
    paginating (maxRecordCount=1000)."""
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_linhas_transmissao_{run_id}"
    os.makedirs(work_dir, exist_ok=True)

    all_features = []
    offset = 0
    batch_size = 1000
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "outSR": "4674",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
        }
        logging.info(f"Querying SIGEL API, offset={offset}...")
        response = government_get(LINHAS_TRANSMISSAO_GOV_URL, params=params, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        logging.info(f"  Retrieved {len(features)} features (total: {len(all_features)})")

        if len(features) < batch_size:
            break
        offset += batch_size

    geojson_data = {
        "type": "FeatureCollection",
        "features": all_features
    }

    extract_path = os.path.join(work_dir, "linhas_transmissao.geojson")
    with open(extract_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False)

    logging.info(f"Total features downloaded: {len(all_features)}")
    return extract_path

def transform_linhas_transmissao(**kwargs) -> str:
    """Transform: reads the GeoJSON, extracts the fields and saves them to a temporary JSON."""
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_linhas_transmissao')

    logging.info(f"Reading GeoJSON: {extract_path}")
    gdf = gpd.read_file(extract_path)

    # Ensure geometries are in SIRGAS 2000 (EPSG:4674)
    if gdf.crs and gdf.crs.to_epsg() != 4674:
        logging.info(f"Reprojecting from {gdf.crs} to EPSG:4674...")
        gdf = gdf.to_crs(4674)

    data_to_insert = []
    for _, row in gdf.iterrows():
        if not row['geometry'] or row['geometry'].is_empty:
            continue

        props_raw = row.drop('geometry').to_dict()
        props = {str(k).lower(): (None if (isinstance(v, float) and v != v) else v) for k, v in props_raw.items()}

        data_to_insert.append({
            "nome_linha": props.get('nome') or props.get('nome_linha') or props.get('name') or props.get('nomelt'),
            "operador": props.get('operador') or props.get('operator') or props.get('agente') or props.get('agenteproprietario'),
            "tensao": str(props.get('tensao') or props.get('tensaokv') or props.get('voltage') or props.get('tensaonominalkv') or ''),
            "situacao": props.get('situacao') or props.get('sit_oper') or props.get('status') or props.get('situacaooperacao'),
            "geom_wkt": row['geometry'].wkt
        })

    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_linhas_transmissao.json")

    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)

    return transformed_file

def load_linhas_transmissao(**kwargs) -> None:
    """Load: inserts the data into PostGIS and cleans up temporary files."""
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_linhas_transmissao')

    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_to_insert = [
        (
            d["nome_linha"],
            d["operador"],
            d["tensao"],
            d["situacao"],
            d["geom_wkt"]
        )
        for d in data
    ]

    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()

    logging.info("Truncating table and inserting new records...")
    cursor.execute("""
        TRUNCATE TABLE mesa_a.vetor_gov_linhas_transmissao RESTART IDENTITY;
    """)

    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_linhas_transmissao (nome_linha, operador, tensao, situacao, geom)
        VALUES (%s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)

    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded government transmission lines into the database!")

    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_linhas_transmissao",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Runs manually
    catchup=False,
    tags=["geodata", "aneel", "linhas_transmissao"]
) as dag:

    extract_task = PythonOperator(
        task_id="extract_linhas_transmissao",
        python_callable=extract_linhas_transmissao
    )

    transform_task = PythonOperator(
        task_id="transform_linhas_transmissao",
        python_callable=transform_linhas_transmissao
    )

    load_task = PythonOperator(
        task_id="load_linhas_transmissao",
        python_callable=load_linhas_transmissao
    )

    extract_task >> transform_task >> load_task
