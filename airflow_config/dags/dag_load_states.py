"""
DAG to automate the download, extraction, and database insertion of State Boundaries.
Downloads a Shapefile from the IBGE FTP, processes it using GeoPandas, 
and loads it into the mesa_a.vetor_limites_estaduais PostGIS table.
"""
import os
import zipfile
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
# Dynamically adds the 'plugins' directory to Python's path
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

# Import URLs from the centralized configuration module (now located in plugins/)
from config_urls import IBGE_STATES_URL

def extract_states(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP, extracts it, and returns the path to the extracted directory.
    """
    # Create a unique temporary directory based on the DAG run ID
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_states_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "states.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {IBGE_STATES_URL}...")
    response = requests.get(IBGE_STATES_URL, stream=True, verify=False)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_states(**kwargs) -> str:
    """
    Task 2: Transform
    Reads the shapefile with GeoPandas, extracts fields, and saves to a temporary JSON.
    """
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_states')
    
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
            "ibge_code": row['CD_UF'],
            "state_name": row['NM_UF'],
            "state_abbr": row['SIGLA_UF'],
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_states.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f)
        
    return transformed_file

def load_states(**kwargs) -> None:
    """
    Task 3: Load
    Reads the JSON file, inserts data into PostGIS, and cleans up the temporary directory.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_states')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (d["ibge_code"], d["state_name"], d["state_abbr"], d["geom_wkt"]) 
        for d in data
    ]
    
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Truncating table and inserting new boundaries...")
    cursor.execute("TRUNCATE TABLE mesa_a.vetor_limites_estaduais RESTART IDENTITY;")
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_limites_estaduais (codigo_ibge, nome_estado, sigla_estado, geom)
        VALUES (%s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded state boundaries into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_state_boundaries",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "ibge", "states"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_states",
        python_callable=extract_states
    )
    
    transform_task = PythonOperator(
        task_id="transform_states",
        python_callable=transform_states
    )
    
    load_task = PythonOperator(
        task_id="load_states",
        python_callable=load_states
    )
    
    extract_task >> transform_task >> load_task
