"""
DAG to automate the download, extraction, and database insertion of Brazil's CAR Property Areas (SICAR).
Downloads Shapefiles for all 27 Brazilian states from the geoserver.car.gov.br WFS service,
processes them using GeoPandas, and loads them into the mesa_a.vetor_gov_sicar_imoveis PostGIS table.
"""
import os
import zipfile
import logging
import requests
import json
import shutil
import pandas as pd
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import geopandas as gpd
from psycopg2.extras import execute_batch

import sys
import ssl
from requests.adapters import HTTPAdapter

class CustomSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ssl_context = ssl.create_default_context()
        # geoserver.car.gov.br requires legacy ciphers (SECLEVEL=0)
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=0')
        ssl_context.check_hostname = False
        kwargs["ssl_context"] = ssl_context
        return super().init_poolmanager(*args, **kwargs)

# Dynamically adds the 'plugins' directory to Python's path
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

# Import URL template from the centralized configuration module
from config_urls import SICAR_STATE_URL_TEMPLATE

# List of all 27 Brazilian States / Federative Units
ESTADOS = [
    'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 
    'mt', 'ms', 'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 
    'rs', 'ro', 'rr', 'sc', 'sp', 'se', 'to'
]

def extract_sicar(**kwargs) -> str:
    """
    Task 1: Extract
    Downloads the shapefile ZIP for each of the 27 states and extracts them to subdirectories.
    """
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_sicar_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    headers = {"User-Agent": "GeoAvia-MESA-Auto/1.0 (Airflow Data Pipeline)"}
    
    session = requests.Session()
    session.mount('https://geoserver.car.gov.br/', CustomSSLAdapter())
    
    for state in ESTADOS:
        state_upper = state.upper()
        state_dir = os.path.join(work_dir, state)
        os.makedirs(state_dir, exist_ok=True)
        
        url = SICAR_STATE_URL_TEMPLATE.format(state=state)
        zip_path = os.path.join(state_dir, f"sicar_{state}.zip")
        extract_path = os.path.join(state_dir, "extracted")
        
        logging.info(f"Downloading SICAR data for {state_upper} from {url}...")
        try:
            # verify=False is used because government geoservers often have certificate authority issues
            response = session.get(url, stream=True, verify=False, headers=headers, timeout=180)
            response.raise_for_status()
            
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info(f"Extracting ZIP file for {state_upper}...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
                
            # Remove zip file to save space
            os.remove(zip_path)
            
        except Exception as e:
            logging.error(f"Failed to download/extract SICAR data for state {state_upper}: {e}")
            raise e
            
    return work_dir

def transform_sicar(**kwargs) -> str:
    """
    Task 2: Transform
    Reads each state's shapefile with GeoPandas, normalizes columns to Portuguese, 
    and saves a combined JSON representation.
    """
    ti = kwargs['ti']
    work_dir = ti.xcom_pull(task_ids='extract_sicar')
    
    data_to_insert = []
    
    for state in ESTADOS:
        state_upper = state.upper()
        state_extracted_dir = os.path.join(work_dir, state, "extracted")
        
        shp_file = None
        for root, _, files in os.walk(state_extracted_dir):
            for file in files:
                if file.lower().endswith(".shp"):
                    shp_file = os.path.join(root, file)
                    break
                    
        if not shp_file:
            logging.warning(f"Shapefile (.shp) not found for state {state_upper} under {state_extracted_dir}. Skipping.")
            continue
            
        logging.info(f"Reading Shapefile for {state_upper}: {shp_file}")
        try:
            gdf = gpd.read_file(shp_file)
        except Exception as e:
            logging.error(f"Failed to read shapefile for state {state_upper}: {e}")
            raise e
        
        # Ensure geometries are in SIRGAS 2000 (EPSG:4674)
        if gdf.crs and gdf.crs.to_epsg() != 4674:
            logging.info(f"Reprojecting {state_upper} from {gdf.crs} to EPSG:4674...")
            gdf = gdf.to_crs(4674)
            
        for _, row in gdf.iterrows():
            if not row['geometry'] or row['geometry'].is_empty:
                continue
                
            codigo_imovel = row.get('cod_imovel')
            if isinstance(codigo_imovel, str):
                codigo_imovel = codigo_imovel.strip()
            else:
                continue # Skip if unique key is missing
                
            status_imovel = row.get('status_imo')
            if isinstance(status_imovel, str):
                status_imovel = status_imovel.strip()
                
            # Parse dates
            data_criacao = row.get('dat_criaca')
            if pd.isnull(data_criacao):
                data_criacao = None
            elif hasattr(data_criacao, 'isoformat'):
                data_criacao = data_criacao.isoformat()
            elif isinstance(data_criacao, str):
                data_criacao = data_criacao.strip()
                if data_criacao == 'NaT':
                    data_criacao = None
            else:
                data_criacao = None
                
            data_atualizacao = row.get('data_atual')
            if pd.isnull(data_atualizacao):
                data_atualizacao = None
            elif hasattr(data_atualizacao, 'isoformat'):
                data_atualizacao = data_atualizacao.isoformat()
            elif isinstance(data_atualizacao, str):
                data_atualizacao = data_atualizacao.strip()
                if data_atualizacao == 'NaT':
                    data_atualizacao = None
            else:
                data_atualizacao = None
                
            area_hectares = row.get('area')
            if pd.isnull(area_hectares):
                area_hectares = None
            elif area_hectares is not None:
                try:
                    area_hectares = float(area_hectares)
                except ValueError:
                    area_hectares = None
                    
            condicao_analise = row.get('condicao')
            if isinstance(condicao_analise, str):
                condicao_analise = condicao_analise.strip()
                
            uf_val = row.get('uf') or state_upper
            if isinstance(uf_val, str):
                uf_val = uf_val.strip().upper()[:2]
                
            municipio = row.get('municipio')
            if isinstance(municipio, str):
                municipio = municipio.strip()
                
            codigo_municipio = row.get('cod_munici')
            if pd.isnull(codigo_municipio):
                codigo_municipio = None
            elif codigo_municipio is not None:
                try:
                    codigo_municipio = int(float(str(codigo_municipio).strip()))
                except ValueError:
                    codigo_municipio = None
                    
            modulo_fiscal = row.get('m_fiscal')
            if pd.isnull(modulo_fiscal):
                modulo_fiscal = None
            elif modulo_fiscal is not None:
                try:
                    modulo_fiscal = float(modulo_fiscal)
                except ValueError:
                    modulo_fiscal = None
                    
            tipo_imovel = row.get('tipo_imove')
            if isinstance(tipo_imovel, str):
                tipo_imovel = tipo_imovel.strip()
                
            data_to_insert.append({
                "codigo_imovel": codigo_imovel,
                "status_imovel": status_imovel,
                "data_criacao": data_criacao,
                "data_atualizacao": data_atualizacao,
                "area_hectares": area_hectares,
                "condicao_analise": condicao_analise,
                "uf": uf_val,
                "municipio": municipio,
                "codigo_municipio": codigo_municipio,
                "modulo_fiscal": modulo_fiscal,
                "tipo_imovel": tipo_imovel,
                "geom_wkt": row['geometry'].wkt
            })
            
    transformed_file = os.path.join(work_dir, "transformed_sicar.json")
    logging.info(f"Saving {len(data_to_insert)} total transformed records into JSON...")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)
        
    return transformed_file

def load_sicar(**kwargs) -> None:
    """
    Task 3: Load
    Truncates the target table and inserts all combined records into PostGIS using ST_Multi.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_sicar')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (
            d["codigo_imovel"],
            d["status_imovel"],
            d["data_criacao"],
            d["data_atualizacao"],
            d["area_hectares"],
            d["condicao_analise"],
            d["uf"],
            d["municipio"],
            d["codigo_municipio"],
            d["modulo_fiscal"],
            d["tipo_imovel"],
            d["geom_wkt"]
        ) 
        for d in data
    ]
    
    if not data_to_insert:
        logging.warning("No valid SICAR records found to insert. Skipping database operations.")
        return
        
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Truncating table and inserting new records...")
    cursor.execute("""
        TRUNCATE TABLE mesa_a.vetor_gov_sicar_imoveis RESTART IDENTITY;
    """)
    
    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_sicar_imoveis (
            codigo_imovel, status_imovel, data_criacao, data_atualizacao, 
            area_hectares, condicao_analise, uf, municipio, 
            codigo_municipio, modulo_fiscal, tipo_imovel, geom
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    logging.info(f"Inserting {len(data_to_insert)} records into mesa_a.vetor_gov_sicar_imoveis...")
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded SICAR data into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_gov_sicar",
    start_date=datetime(2024, 1, 1),
    schedule=None, # Runs manually
    catchup=False,
    tags=["geodata", "sicar", "imoveis"]
) as dag:
    
    extract_task = PythonOperator(
        task_id="extract_sicar",
        python_callable=extract_sicar
    )
    
    transform_task = PythonOperator(
        task_id="transform_sicar",
        python_callable=transform_sicar
    )
    
    load_task = PythonOperator(
        task_id="load_sicar",
        python_callable=load_sicar
    )
    
    extract_task >> transform_task >> load_task
