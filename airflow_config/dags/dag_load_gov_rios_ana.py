"""
DAG to automate the download, extraction, and database insertion of Brazil's River Network (Rios).
Downloads the BHO (Base Hidrográfica Ottocodificada) shapefile from ANA/SNIRH, processes it using
GeoPandas, and loads it into the mesa_a.vetor_gov_rios_ana PostGIS table.
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

# Import URL from the centralized configuration module
from config_urls import RIOS_ANA_URL

def extract_rios_ana(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP, extracts it, and returns the path to the extracted directory.
    """
    # Create a unique temporary directory based on the DAG run ID
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_rios_ana_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "rios_ana.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {RIOS_ANA_URL}...")
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    response = requests.get(RIOS_ANA_URL, stream=True, verify=False, headers=headers)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_rios_ana(**kwargs) -> str:
    """
    Task 2: Transform
    Reads the shapefile with GeoPandas, extracts fields into a JSONB structure, 
    and saves to a temporary JSON.
    """
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_rios_ana')
    
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
    
    # Ensure geometries are in SIRGAS 2000 (EPSG:4674)
    # Source data is typically in SAD69 (EPSG:4291), so reprojection is expected
    if gdf.crs and gdf.crs.to_epsg() != 4674:
        logging.info(f"Reprojecting from {gdf.crs} to EPSG:4674...")
        gdf = gdf.to_crs(4674)
    
    data_to_insert = []
    for _, row in gdf.iterrows():
        if not row['geometry'] or row['geometry'].is_empty:
            continue
            
        props_raw = row.drop('geometry').to_dict()
        # Convert all keys to lowercase to avoid issues if the shapefile changes case
        props = {str(k).lower(): (None if (isinstance(v, float) and v != v) else v) for k, v in props_raw.items()}
        
        data_to_insert.append({
            "nome_rio": props.get('rio_nm_com') or props.get('rio_nm_completo') or props.get('nome_rio') or props.get('norio'),
            "cocurso": props.get('cocursodag') or props.get('cocurso'),
            "corio": props.get('corio') or props.get('rio_cd'),
            "nucompam": props.get('nucompam'),
            "nuareaam": props.get('nuareaam'),
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_rios_ana.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)
        
    return transformed_file

def load_rios_ana(**kwargs) -> None:
    """
    Task 3: Load
    Creates the target table if missing, inserts data into PostGIS, and cleans up.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_rios_ana')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (
            d["nome_rio"],
            d["cocurso"],
            d["corio"],
            d["nucompam"],
            d["nuareaam"],
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
        TRUNCATE TABLE mesa_a.vetor_gov_rios_ana RESTART IDENTITY;
    """)
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_rios_ana (nome_rio, cocurso, corio, nucompam, nuareaam, geom)
        VALUES (%s, %s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded government river data into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_rios_ana",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "ana", "rios"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_rios_ana",
        python_callable=extract_rios_ana
    )
    
    transform_task = PythonOperator(
        task_id="transform_rios_ana",
        python_callable=transform_rios_ana
    )
    
    load_task = PythonOperator(
        task_id="load_rios_ana",
        python_callable=load_rios_ana
    )
    
    extract_task >> transform_task >> load_task
