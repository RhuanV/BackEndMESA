"""
Incremental OSM update DAG using Geofabrik replication diffs.
"""

import os
import logging
import subprocess
import shutil
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset

DATA_DIR = "/opt/airflow/data"
osm_dataset = Dataset("file:///opt/airflow/data/brazil-latest.osm.pbf")

import sys
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

from config_urls import GEODIFF_URL

def update_osm_diffs(**kwargs):

    pbf_path = os.path.join(DATA_DIR, "brazil-latest.osm.pbf")

    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"Base file not found: {pbf_path}. Execute the download DAG first.")
        
    backup_path = f"{pbf_path}.bak"
    logging.info(f"Creating safety backup at {backup_path}...")
    shutil.copy2(pbf_path, backup_path)
    
    logging.info(f"Incrementally updating {pbf_path} from {GEODIFF_URL}...")
    
    # pyosmium-up-to-date automatically discovers the PBF date, downloads the diffs, and applies them.
    cmd = [
        "pyosmium-up-to-date",
        pbf_path,
        "--ignore-osmosis-headers",
        "--server", GEODIFF_URL,
        "--size", "10000" # Increased size limit to ensure it downloads everything at once
    ]
    
    try:
        # Execute the command capturing terminal logs to find the exact reason on failure
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            logging.info(f"STDOUT: {result.stdout.strip()}")
        if result.stderr:
            logging.warning(f"STDERR: {result.stderr.strip()}")
            
        if result.returncode == 0:
            logging.info("Incremental update completed successfully!")
        elif result.returncode == 1:
            logging.warning("pyosmium returned code 1 (partial update due to size limit reached).")
        elif result.returncode == 3:
            logging.info("The PBF file is already fully up-to-date. No new updates were found.")
        else:
            raise RuntimeError(f"pyosmium-up-to-date failed with code {result.returncode}.")
            
        # If execution is successful and reaches here, delete the backup to save space
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
    except Exception as e:
        logging.error(f"Catastrophic error detected: {e}")
        if os.path.exists(backup_path):
            logging.warning("Restoring PBF file from safety backup...")
            shutil.move(backup_path, pbf_path)
        raise


with DAG(
    dag_id="update_osm_diffs",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["osm", "incremental", "geofabrik"]
) as dag:

    update_task = PythonOperator(
        task_id="update_osm_diffs",
        python_callable=update_osm_diffs,
        outlets=[osm_dataset]
    )
