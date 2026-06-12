"""
DAG to automate the download, extraction, and database insertion of Municipality Boundaries.
Downloads a Shapefile from the IBGE FTP, processes it using GeoPandas, 
and loads it into the mesa_a.vetor_limites_municipais PostGIS table.
"""
import os
import zipfile
import logging
import requests
import json
import shutil
from datetime import datetime
from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import geopandas as gpd
from psycopg2.extras import execute_batch

# Dataset emitted when municipality_boundaries is loaded. Consumed by
# dag_refresh_resolution_views to keep the simplified views in sync.
municipalities_dataset = Dataset("postgres://geoavia_main_db/municipality_boundaries")

import sys
# Dynamically adds the 'plugins' directory to Python's path
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

# Import URLs from the centralized configuration module (now located in plugins/)
from config_urls import IBGE_MUNICIPALITIES_URL

def extract_municipalities(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP, extracts it, and returns the path to the extracted directory.
    """
    # Create a unique temporary directory based on the DAG run ID
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_municipalities_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "municipalities.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {IBGE_MUNICIPALITIES_URL}...")
    response = requests.get(IBGE_MUNICIPALITIES_URL, stream=True, verify=False)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_municipalities(**kwargs) -> str:
    """
    Task 2: Transform
    Reads the shapefile with GeoPandas, extracts fields, and saves to a temporary JSON.
    """
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_municipalities')
    
    shp_file = None
    for root, _, files in os.walk(extract_path):
        for file in files:
            if file.lower().endswith(".shp"):
                shp_file = os.path.join(root, file)
                break
                
    if not shp_file:
        raise FileNotFoundError("Shapefile (.shp) not found in the downloaded ZIP.")
        
    logging.info(f"Reading Shapefile: {shp_file}")
    gdf = gpd.read_file(shp_file)
    
    data_to_insert = []
    for _, row in gdf.iterrows():
        data_to_insert.append({
            "ibge_code": row['CD_MUN'],
            "municipality_name": row['NM_MUN'],
            "state_abbr": row['SIGLA_UF'],
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_municipalities.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f)
        
    return transformed_file

def load_municipalities(**kwargs) -> None:
    """
    Task 3: Load
    Reads the JSON file, inserts data into PostGIS, and cleans up the temporary directory.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_municipalities')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (d["ibge_code"], d["municipality_name"], d["state_abbr"], d["geom_wkt"]) 
        for d in data
    ]
    
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Truncating table and inserting new boundaries...")
    cursor.execute("TRUNCATE TABLE mesa_a.vetor_limites_municipais RESTART IDENTITY;")
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_limites_municipais (codigo_ibge, nome_municipio, sigla_estado, geom)
        VALUES (%s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded municipality boundaries into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_municipality_boundaries",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "ibge", "municipalities"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_municipalities",
        python_callable=extract_municipalities
    )
    
    transform_task = PythonOperator(
        task_id="transform_municipalities",
        python_callable=transform_municipalities
    )
    
    load_task = PythonOperator(
        task_id="load_municipalities",
        python_callable=load_municipalities,
        outlets=[municipalities_dataset]
    )
    
    extract_task >> transform_task >> load_task