"""
DAG to download the latest OpenStreetMap PBF binary for Brazil from Geofabrik.
This file serves as the local database for all subsequent OSM processing DAGs.
"""
import os
import logging
import requests
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

from config_urls import GEOFABRIK_BRAZIL_URL

def download_geofabrik_pbf(**kwargs):
    # We save the file in a dedicated data volume to avoid overloading the DAG parser
    data_dir = "/opt/airflow/data"
    os.makedirs(data_dir, exist_ok=True)
    
    pbf_path = os.path.join(data_dir, "brazil-latest.osm.pbf")
    tmp_path = f"{pbf_path}.tmp"
    
    logging.info(f"Downloading OSM PBF from {GEOFABRIK_BRAZIL_URL} to {pbf_path}...")
    
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    response = requests.get(GEOFABRIK_BRAZIL_URL, stream=True, headers=headers)
    response.raise_for_status()
    
    with open(tmp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    os.rename(tmp_path, pbf_path)
    logging.info("Download completed successfully!")

with DAG(
    dag_id="download_geofabrik_data",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "osm", "geofabrik"]
) as dag:
    
    download_task = PythonOperator(
        task_id="download_geofabrik_pbf",
        python_callable=download_geofabrik_pbf
    )
