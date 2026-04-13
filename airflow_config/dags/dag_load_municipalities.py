"""
DAG to automate the download, extraction, and database insertion of Municipality Boundaries.
Downloads a Shapefile from the IBGE FTP, processes it using GeoPandas, 
and loads it into the municipality_boundaries PostGIS table.
"""
import os
import zipfile
import tempfile
import logging
import requests
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import geopandas as gpd
from psycopg2.extras import execute_batch

import sys
# Dynamically adds the 'plugins' directory to Python's path
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

# Import URLs from the centralized configuration module (now located in plugins/)
from config_urls import IBGE_MUNICIPALITIES_URL

def download_and_process_municipalities() -> None:
    """
    Downloads the shapefile ZIP to a temporary directory, extracts it, 
    reads it with GeoPandas, and inserts into the database.
    """
    # Create a temporary directory that will be automatically deleted after the function ends
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "municipalities.zip")
        extract_path = os.path.join(tmp_dir, "extracted")
        
        # 1. Download the ZIP file
        logging.info(f"Downloading from {IBGE_MUNICIPALITIES_URL}...")
        # Disable SSL verification temporarily if IBGE's certificate has issues
        response = requests.get(IBGE_MUNICIPALITIES_URL, stream=True, verify=False)
        response.raise_for_status()
        
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # 2. Extract the ZIP file
        logging.info("Extracting ZIP file...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
            
        # 3. Find the .shp file dynamically
        shp_file = None
        for root, _, files in os.walk(extract_path):
            for file in files:
                if file.lower().endswith(".shp"):
                    shp_file = os.path.join(root, file)
                    break
                    
        if not shp_file:
            raise FileNotFoundError("Shapefile (.shp) not found in the downloaded ZIP.")
            
        # 4. Read with GeoPandas
        logging.info(f"Reading Shapefile: {shp_file}")
        gdf = gpd.read_file(shp_file)
        
        data_to_insert = []
        for _, row in gdf.iterrows():
            data_to_insert.append((
                row['CD_MUN'],
                row['NM_MUN'],
                row['SIGLA_UF'],
                row['geometry'].wkt
            ))
            
        # 5. Connect to database using Airflow Connections
        logging.info("Connecting to database via Airflow Connection...")
        # This searches for a connection named 'geoavia_main_conn' in Airflow UI
        hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
        conn = hook.get_conn()
        cursor = conn.cursor()
        
        # 6. Clear table and Insert Data
        logging.info("Truncating table and inserting new boundaries...")
        cursor.execute("TRUNCATE TABLE municipality_boundaries RESTART IDENTITY;")
        
        sql_insert = """
            INSERT INTO municipality_boundaries (ibge_code, municipality_name, state_abbr, geom)
            VALUES (%s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
        """
        execute_batch(cursor, sql_insert, data_to_insert)
        
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("Successfully loaded municipality boundaries into the database!")

with DAG(
    dag_id="load_municipality_boundaries",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None, # Runs manually
    catchup=False,
    tags=["geodata", "ibge", "municipalities"]
) as dag:
    
    task_load_municipalities = PythonOperator(
        task_id="download_and_process_municipalities",
        python_callable=download_and_process_municipalities
    )