"""
DAG to automate the download, extraction, and database insertion of Brazil's Railway Network.
Downloads a Shapefile from the Ministério dos Transportes, processes it using GeoPandas, 
and loads it into the gov_railways PostGIS table.
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
from config_urls import RAILWAY_BRAZIL_URL

def extract_railways(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP, extracts it, and returns the path to the extracted directory.
    """
    # Create a unique temporary directory based on the DAG run ID
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_railways_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "railways.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {RAILWAY_BRAZIL_URL}...")
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    response = requests.get(RAILWAY_BRAZIL_URL, stream=True, verify=False, headers=headers)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_railways(**kwargs) -> str:
    """
    Task 2: Transform
    Reads the shapefile with GeoPandas, extracts fields into a JSONB structure, 
    and saves to a temporary JSON.
    """
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_railways')
    
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
            "uf": props.get('uf'),
            "nome": props.get('nome'),
            "sigla": props.get('sigla'),
            "bitola": props.get('bitola'),
            "extensao": props.get('extensao'),
            "municipio": props.get('municipio'),
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_railways.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)
        
    return transformed_file

def load_railways(**kwargs) -> None:
    """
    Task 3: Load
    Creates the target table if missing, inserts data into PostGIS, and cleans up.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_railways')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (
            d["uf"],
            d["nome"],
            d["sigla"],
            d["bitola"],
            d["extensao"],
            d["municipio"],
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
        TRUNCATE TABLE gov_railways RESTART IDENTITY;
    """)
    
    sql_insert = """
        INSERT INTO gov_railways (uf, nome, sigla, bitola, extensao, municipio, geom)
        VALUES (%s, %s, %s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded government railways into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_railways",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None, # Runs manually
    catchup=False,
    tags=["geodata", "mt", "railways"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_railways",
        python_callable=extract_railways
    )
    
    transform_task = PythonOperator(
        task_id="transform_railways",
        python_callable=transform_railways
    )
    
    load_task = PythonOperator(
        task_id="load_railways",
        python_callable=load_railways
    )
    
    extract_task >> transform_task >> load_task