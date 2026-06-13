"""
DAG to automate the download, extraction, and database insertion of Brazil's Indigenous Lands
(Terra Indígena). Downloads a Shapefile from FUNAI's GeoServer, processes it using GeoPandas,
and loads it into the mesa_a.vetor_gov_terra_indigena PostGIS table.
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
from config_urls import TERRA_INDIGENA_URL

def extract_terra_indigena(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP, extracts it, and returns the path to the extracted directory.
    """
    # Create a unique temporary directory based on the DAG run ID
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_terra_indigena_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    zip_path = os.path.join(work_dir, "terra_indigena.zip")
    extract_path = os.path.join(work_dir, "extracted")
    
    logging.info(f"Downloading from {TERRA_INDIGENA_URL}...")
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    response = requests.get(TERRA_INDIGENA_URL, stream=True, verify=False, headers=headers)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logging.info("Extracting ZIP file...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
        
    return extract_path

def transform_terra_indigena(**kwargs) -> str:
    """
    Task 2: Transform
    Reads the shapefile with GeoPandas, extracts fields into a JSONB structure, 
    and saves to a temporary JSON.
    """
    ti = kwargs['ti']
    extract_path = ti.xcom_pull(task_ids='extract_terra_indigena')
    
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
            "nome_ti": props.get('terrai_nom') or props.get('nome_ti') or props.get('nome'),
            "etnia": props.get('etnia_nome') or props.get('etnia'),
            "municipio": props.get('municipio_') or props.get('municipio'),
            "uf": props.get('uf_sigla') or props.get('uf'),
            "situacao_juridica": props.get('fase_ti') or props.get('situacao_juridica'),
            "fase": props.get('fase_ti') or props.get('fase'),
            "modalidade": props.get('modalidade') or props.get('mod_'),
            "superficie_ha": props.get('superfic_1') or props.get('superficie') or props.get('superficie_ha'),
            "geom_wkt": row['geometry'].wkt
        })
        
    work_dir = os.path.dirname(extract_path)
    transformed_file = os.path.join(work_dir, "transformed_terra_indigena.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)
        
    return transformed_file

def load_terra_indigena(**kwargs) -> None:
    """
    Task 3: Load
    Creates the target table if missing, inserts data into PostGIS, and cleans up.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_terra_indigena')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (
            d["nome_ti"],
            d["etnia"],
            d["municipio"],
            d["uf"],
            d["situacao_juridica"],
            d["fase"],
            d["modalidade"],
            d["superficie_ha"],
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
        TRUNCATE TABLE mesa_a.vetor_gov_terra_indigena RESTART IDENTITY;
    """)
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_terra_indigena (nome_ti, etnia, municipio, uf, situacao_juridica, fase, modalidade, superficie_ha, geom)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded government indigenous lands into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_terra_indigena",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "funai", "terra_indigena"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_terra_indigena",
        python_callable=extract_terra_indigena
    )
    
    transform_task = PythonOperator(
        task_id="transform_terra_indigena",
        python_callable=transform_terra_indigena
    )
    
    load_task = PythonOperator(
        task_id="load_terra_indigena",
        python_callable=load_terra_indigena
    )
    
    extract_task >> transform_task >> load_task
