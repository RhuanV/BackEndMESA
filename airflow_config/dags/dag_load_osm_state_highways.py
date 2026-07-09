"""
Extracts state highways from the OSM PBF (Geofabrik) and loads them into mesa_a.vetor_osm_rodovias_estaduais.
"""
import os
import json
import logging
import subprocess
import shutil
import re
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_batch

import sys
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

osm_dataset = Dataset("file:///opt/airflow/data/brazil-latest.osm.pbf")

def check_pbf_exists() -> None:
    """Checks whether the Brazil PBF has already been downloaded by the Geofabrik DAG."""
    pbf_path = "/opt/airflow/data/brazil-latest.osm.pbf"
    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"Brazil PBF dependency missing at {pbf_path}. Run 'download_geofabrik_data' DAG first.")
    logging.info(f"Dependency met: PBF file found at {pbf_path}.")

def extract_and_transform_state_highways(**kwargs) -> str:
    """Filters highways with a state ref (non-BR) from the PBF and produces the processed JSON."""
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_osm_state_highways_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    pbf_path = "/opt/airflow/data/brazil-latest.osm.pbf"
    filtered_pbf = os.path.join(work_dir, "state_highways_filtered.osm.pbf")
    geojson_path = os.path.join(work_dir, "state_highways.geojson")
    
    osmium_bin = shutil.which("osmium")
    if not osmium_bin:
        raise RuntimeError("Executable 'osmium' not found. Verify the installation of 'osmium-tool' in the Dockerfile and ensure the image was rebuilt (--build).")

    logging.info("Filtering features using osmium tags-filter...")
    # Extract ways and relations with a 'ref' tag
    subprocess.run([
        osmium_bin, "tags-filter", pbf_path, 
        "w/ref", "r/ref",
        "-o", filtered_pbf, "--overwrite"
    ], check=True)
    
    logging.info("Exporting filtered data to GeoJSON...")
    
    config_path = os.path.join(work_dir, "osmium_export_config.json")
    export_config = {
        "attributes": {
            "type": True,
            "id": True,
            "version": False,
            "changeset": False,
            "timestamp": False,
            "uid": False,
            "user": False,
            "way_nodes": False
        },
        "point_tags": False,
        "linear_tags": True,
        "area_tags": False,
        "exclude_tags": [],
        "include_tags": []
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(export_config, f)

    subprocess.run([
        osmium_bin, "export", filtered_pbf, 
        "-c", config_path,
        "-o", geojson_path, "--overwrite"
    ], check=True)
    
    logging.info("Parsing GeoJSON to prepare WKT formats for database insertion...")
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = []
    # Matches refs like SP-348, MG 050, RJ123
    state_pattern = re.compile(r"^[A-Z]{2}[- ]?[0-9]+")
    
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry')
        
        ref = str(props.get('ref', '')).strip().upper()
        highway = props.get('highway')
        
        # Keep only highways with a state ref that do not start with BR
        if not highway or not state_pattern.search(ref) or ref.startswith("BR"):
            continue
        
        feature_id = feature.get('id')
        if feature_id is None:
            feature_id = props.get('@id')
        if feature_id is None:
            feature_id = props.get('osm_id')
            
        feature_id_str = str(feature_id) if feature_id is not None else ''
        
        osm_id = None
        if feature_id_str.startswith("way/"):
            osm_id = int(feature_id_str.replace("way/", ""))
        elif feature_id_str.startswith("relation/"):
            osm_id = -int(feature_id_str.replace("relation/", ""))
        elif feature_id_str.lstrip('-').isdigit():
            osm_id = int(feature_id_str)
            
        if geom and osm_id is not None:
            geom_wkt = None
            if geom['type'] == 'LineString':
                coords = [f"{pt[0]} {pt[1]}" for pt in geom['coordinates']]
                geom_wkt = f"LINESTRING({', '.join(coords)})"
            elif geom['type'] == 'MultiLineString':
                lines = []
                for line in geom['coordinates']:
                    coords = [f"{pt[0]} {pt[1]}" for pt in line]
                    lines.append(f"({', '.join(coords)})")
                geom_wkt = f"MULTILINESTRING({', '.join(lines)})"
                
            if geom_wkt:
                data_to_insert.append({
                    "osm_id": osm_id,
                    "name": props.get('name', ''),
                    "ref": ref,
                    "highway": highway,
                    "geom_wkt": geom_wkt
                })
            
    logging.info(f"Successfully extracted {len(data_to_insert)} state highway features.")
    transformed_file = os.path.join(work_dir, "transformed_state_highways.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f)
        
    return transformed_file

def load_osm_state_highways(**kwargs) -> None:
    """Reads the transformed JSON and upserts the data into PostGIS."""
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='extract_and_transform_state_highways')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (d["osm_id"], d["name"], d["ref"], d["highway"], d["geom_wkt"]) 
        for d in data
    ]
    
    if not data_to_insert:
        logging.warning("No valid state highway features found to insert.")
        return
        
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Creating temporary table for loading...")
    cursor.execute("""
        CREATE TEMP TABLE temp_osm_state_highways (
            osm_id BIGINT,
            nome VARCHAR(255),
            referencia VARCHAR(50),
            tipo_rodovia VARCHAR(50),
            geom_wkt TEXT
        ) ON COMMIT DROP;
    """)
    
    sql_insert_temp = """
        INSERT INTO temp_osm_state_highways (osm_id, nome, referencia, tipo_rodovia, geom_wkt)
        VALUES (%s, %s, %s, %s, %s)
    """
    logging.info(f"Upserting {len(data_to_insert)} records into the temporary table...")
    execute_batch(cursor, sql_insert_temp, data_to_insert)
    
    logging.info("Upserting data into main table from temporary table...")
    cursor.execute("""
        INSERT INTO mesa_a.vetor_osm_rodovias_estaduais (osm_id, nome, referencia, tipo_rodovia, geom)
        SELECT DISTINCT ON (osm_id) osm_id, nome, referencia, tipo_rodovia, ST_SetSRID(ST_GeomFromText(geom_wkt), 4674)
        FROM temp_osm_state_highways
        ORDER BY osm_id
        ON CONFLICT (osm_id) DO UPDATE SET
            nome = EXCLUDED.nome,
            referencia = EXCLUDED.referencia,
            tipo_rodovia = EXCLUDED.tipo_rodovia,
            geom = EXCLUDED.geom;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded OSM state highways into the database!")
    
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_osm_state_highways",
    start_date=datetime(2024, 1, 1),
    schedule=[osm_dataset],  # Runs automatically when the PBF is updated
    catchup=False,
    tags=["geodata", "osm", "highways", "state"]
) as dag:
    
    check_dependency_task = PythonOperator(
        task_id="check_geofabrik_dependency",
        python_callable=check_pbf_exists
    )
    
    extract_transform_task = PythonOperator(
        task_id="extract_and_transform_state_highways",
        python_callable=extract_and_transform_state_highways
    )
    
    load_task = PythonOperator(
        task_id="load_osm_state_highways",
        python_callable=load_osm_state_highways
    )
    
    check_dependency_task >> extract_transform_task >> load_task
