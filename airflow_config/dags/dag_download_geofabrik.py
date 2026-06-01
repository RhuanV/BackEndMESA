"""
DAG to download the latest OpenStreetMap PBF binary for Brazil from Geofabrik.
This file serves as the local database for all subsequent OSM processing DAGs.
"""
import os
import logging
import requests
import subprocess
import shutil
from datetime import datetime, timedelta
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
    tmp_path = os.path.join(data_dir, "brazil-latest.tmp.osm.pbf")
    
    logging.info(f"Downloading OSM PBF from {GEOFABRIK_BRAZIL_URL} to {pbf_path}...")
    
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    
    # Resume implementation (Continues interrupted downloads)
    downloaded_size = 0
    if os.path.exists(tmp_path):
        downloaded_size = os.path.getsize(tmp_path)
        logging.info(f"Temporary file found with {downloaded_size} bytes. Requesting resume (Range)...")
        headers["Range"] = f"bytes={downloaded_size}-"
        
    response = requests.get(GEOFABRIK_BRAZIL_URL, stream=True, headers=headers)
    
    if response.status_code == 206:
        mode = "ab"
        logging.info("Server accepted download resume (HTTP 206 Partial Content).")
    elif response.status_code == 200:
        mode = "wb"
        logging.info("Starting download from scratch (HTTP 200 OK).")
    else:
        # If the server returns a different status code (e.g., 416 if the file changed), start from scratch
        logging.warning(f"Unexpected response {response.status_code}. Restarting download from scratch.")
        mode = "wb"
        if "Range" in headers:
            del headers["Range"]
        response = requests.get(GEOFABRIK_BRAZIL_URL, stream=True, headers=headers)
        
    response.raise_for_status()
    
    total_content_length = response.headers.get('content-length')
    if total_content_length is not None:
        total_expected_size = downloaded_size + int(total_content_length) if mode == "ab" else int(total_content_length)
    else:
        total_expected_size = 0
        
    current_size = downloaded_size if mode == "ab" else 0
    last_logged_percent = 0
    
    with open(tmp_path, mode) as f:
        # Increased chunk size to 1MB to make disk writing significantly faster
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                current_size += len(chunk)
                
                if total_expected_size > 0:
                    percent = int((current_size / total_expected_size) * 100)
                    # Log every 5% to avoid log spam
                    if percent >= last_logged_percent + 5:
                        logging.info(f"Download progress: {percent}% ({current_size / (1024*1024):.2f} MB / {total_expected_size / (1024*1024):.2f} MB)")
                        last_logged_percent = percent
                else:
                    # Fallback if server doesn't provide content-length
                    pass
    
    if total_expected_size > 0 and current_size < total_expected_size:
        raise RuntimeError(f"Connection dropped early! Downloaded {current_size} of {total_expected_size} bytes. Will resume on retry.")

    # Integrity validation: ensures the download is not corrupted before applying it
    osmium_bin = shutil.which("osmium")
    if osmium_bin:
        logging.info("Validating the integrity of the newly downloaded file...")
        try:
            subprocess.run([osmium_bin, "fileinfo", tmp_path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Unknown error"
            logging.error(f"Osmium fileinfo failed! STDERR: {error_msg}")
            
            # If we reached 100% but it's still corrupt, we MUST delete it to escape the resume loop
            if total_expected_size > 0 and current_size >= total_expected_size:
                logging.warning("File reached 100% but is corrupt. Deleting to force a fresh download on next retry.")
                os.remove(tmp_path)
                
            raise RuntimeError(f"The downloaded PBF file is corrupted. Osmium error: {error_msg}")
            
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
        python_callable=download_geofabrik_pbf,
        retries=5,
        retry_delay=timedelta(minutes=5)
    )
