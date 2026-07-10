"""
Loads airfields (ANA/SNIRH) into the mesa_a.vetor_gov_aerodromos table.
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
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

from config_urls import AERODROMOS_ANA_URL

def extract_aerodromos(**kwargs) -> str:
    """Extract: downloads and unpacks the ZIP, returning the extracted directory."""
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_aerodromos_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "aerodromos.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {AERODROMOS_ANA_URL}...")
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    response = requests.get(AERODROMOS_ANA_URL, stream=True, verify=False, headers=headers)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_aerodromos(**kwargs) -> str:
    """Transform: reads the shapefile and writes the fields to a temporary JSON."""
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_aerodromos')
    
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
        # Lowercase keys to stay robust if the shapefile changes column casing
        props = {str(k).lower(): (None if (isinstance(v, float) and v != v) else v) for k, v in props_raw.items()}
        
        data_to_insert.append({
            "nome": props.get('aer_nm') or props.get('nome'),
            "municipio": props.get('municipio') or props.get('nm_municip'),
            "uf": props.get('aer_sg_uf') or props.get('uf'),
            "situacao": props.get('aer_tae_cd') or props.get('situacao') or props.get('tipo'),
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_aerodromos.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)
        
    return transformed_file

def load_aerodromos(**kwargs) -> None:
    """Load: inserts the data into PostGIS and cleans up temporary files."""
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_aerodromos')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (
            d["nome"],
            d["municipio"],
            d["uf"],
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
        TRUNCATE TABLE mesa_a.vetor_gov_aerodromos RESTART IDENTITY;
    """)
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_aerodromos (nome, municipio, uf, situacao, geom)
        VALUES (%s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded government airfields into the database!")
    
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_aerodromos",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Runs manually
    catchup=False,
    tags=["geodata", "ana", "aerodromos"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_aerodromos",
        python_callable=extract_aerodromos
    )
    
    transform_task = PythonOperator(
        task_id="transform_aerodromos",
        python_callable=transform_aerodromos
    )
    
    load_task = PythonOperator(
        task_id="load_aerodromos",
        python_callable=load_aerodromos
    )
    
    extract_task >> transform_task >> load_task
