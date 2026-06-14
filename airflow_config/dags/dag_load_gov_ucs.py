"""
DAG to automate the download, extraction, and database insertion of Brazil's Federal Conservation Units (UCs).
Downloads a Shapefile from ICMBio, processes it using GeoPandas, 
and loads it into the mesa_a.vetor_gov_uc PostGIS table.
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
from config_urls import FEDERAL_UCS_BRAZIL_URL

def extract_ucs(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP, extracts it, and returns the path to the extracted directory.
    """
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_ucs_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "ucs.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {FEDERAL_UCS_BRAZIL_URL}...")
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    # verify=False is used because gov.br sometimes has SSL certificate validation issues
    response = requests.get(FEDERAL_UCS_BRAZIL_URL, stream=True, verify=False, headers=headers)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_ucs(**kwargs) -> str:
    """
    Task 2: Transform
    Reads the shapefile with GeoPandas, transforms values to match DB columns,
    and saves to a temporary JSON for database insertion.
    """
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_ucs')
    
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
            
        nome_uc = row.get('nomeuc')
        if isinstance(nome_uc, str):
            nome_uc = nome_uc.strip()
            
        categoria = row.get('categoria_')
        if isinstance(categoria, str):
            categoria = categoria.strip()
            
        esfera = row.get('esferaadm') or 'Federal'
        if isinstance(esfera, str):
            esfera = esfera.strip()
            
        # Parse year of creation
        ano_criacao = row.get('criacaoano')
        if ano_criacao is not None:
            try:
                ano_criacao = int(float(str(ano_criacao).strip()))
            except ValueError:
                ano_criacao = None
        else:
            ano_criacao = None
            
        data_to_insert.append({
            "nome_uc": nome_uc,
            "categoria": categoria,
            "esfera": esfera,
            "ano_criacao": ano_criacao,
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_ucs.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)
        
    return transformed_file

def load_ucs(**kwargs) -> None:
    """
    Task 3: Load
    Truncates the table and inserts data into PostGIS using ST_Multi to normalize geometries.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_ucs')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (
            d["nome_uc"],
            d["categoria"],
            d["esfera"],
            d["ano_criacao"],
            d["geom_wkt"]
        ) 
        for d in data
    ]
    
    if not data_to_insert:
        logging.warning("No valid UC features found to insert. Skipping database operations.")
        return
        
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Truncating table and inserting new records...")
    cursor.execute("""
        TRUNCATE TABLE mesa_a.vetor_gov_uc RESTART IDENTITY;
    """)
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_uc (nome_uc, categoria, esfera, ano_criacao, geom)
        VALUES (%s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded government UCs into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_ucs",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "icmbio", "ucs"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_ucs",
        python_callable=extract_ucs
    )
    
    transform_task = PythonOperator(
        task_id="transform_ucs",
        python_callable=transform_ucs
    )
    
    load_task = PythonOperator(
        task_id="load_ucs",
        python_callable=load_ucs
    )
    
    extract_task >> transform_task >> load_task
