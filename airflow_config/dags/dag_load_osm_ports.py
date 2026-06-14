"""
DAG to automate the extraction and database insertion of Ports from OpenStreetMap.
Uses the local Geofabrik PBF, filters with Osmium Tool, and loads it into a PostGIS table.
"""
import os
import json
import logging
import subprocess
import shutil
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_batch

import sys
# Dynamically adds the 'plugins' directory to Python's path
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

osm_dataset = Dataset("file:///opt/airflow/data/brazil-latest.osm.pbf")

def check_pbf_exists() -> None:
    """
    Task 0: Check Dependency
    Verifies if the Geofabrik DAG has already been executed by checking the PBF file.
    """
    pbf_path = "/opt/airflow/data/brazil-latest.osm.pbf"
    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"Brazil PBF dependency missing at {pbf_path}. Run 'download_geofabrik_data' DAG first.")
    logging.info(f"Dependency met: PBF file found at {pbf_path}.")

def extract_and_transform_ports(**kwargs) -> str:
    """
    Task 1: Extract & Transform
    Reads the local Brazil PBF, filters port features, and exports to a processed JSON.
    """
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_osm_ports_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    pbf_path = "/opt/airflow/data/brazil-latest.osm.pbf"
    filtered_pbf = os.path.join(work_dir, "ports_filtered.osm.pbf")
    geojson_path = os.path.join(work_dir, "ports.geojson")
    
    osmium_bin = shutil.which("osmium")
    if not osmium_bin:
        raise RuntimeError("Executable 'osmium' not found. Verify the installation of 'osmium-tool' in the Dockerfile and ensure the image was rebuilt (--build).")

    logging.info("Filtering features using osmium tags-filter...")
    subprocess.run([
        osmium_bin, "tags-filter", pbf_path, 
        "n/harbour", "w/harbour", "r/harbour",
        "n/industrial=port", "w/industrial=port", "r/industrial=port",
        "n/port", "w/port", "r/port",
        "-o", filtered_pbf, "--overwrite"
    ], check=True)
    
    logging.info("Exporting filtered data to GeoJSON...")
    
    # Create an osmium export config
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
        "point_tags": True,
        "linear_tags": True,
        "area_tags": True,
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
    
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry')
        
        # Robust ID extraction
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
        elif feature_id_str.startswith("node/"):
            osm_id = int(feature_id_str.replace("node/", ""))
        elif props.get('@type') == 'relation' and feature_id_str.lstrip('-').isdigit():
            osm_id = -int(feature_id_str)
        elif feature_id_str.lstrip('-').isdigit():
            osm_id = int(feature_id_str)
            
        if geom and osm_id is not None:
            geom_wkt = None
            if geom['type'] == 'Point':
                geom_wkt = f"POINT({geom['coordinates'][0]} {geom['coordinates'][1]})"
            elif geom['type'] == 'Polygon':
                rings = []
                for ring in geom['coordinates']:
                    coords = [f"{pt[0]} {pt[1]}" for pt in ring]
                    rings.append(f"({', '.join(coords)})")
                geom_wkt = f"POLYGON({', '.join(rings)})"
            elif geom['type'] == 'MultiPolygon':
                polys = []
                for poly in geom['coordinates']:
                    rings = []
                    for ring in poly:
                        coords = [f"{pt[0]} {pt[1]}" for pt in ring]
                        rings.append(f"({', '.join(coords)})")
                    polys.append(f"({', '.join(rings)})")
                geom_wkt = f"MULTIPOLYGON({', '.join(polys)})"
                
            if geom_wkt:
                # Extract state/UF from tags if present
                uf_val = props.get('addr:state') or props.get('addr:province') or props.get('addr:region')
                if isinstance(uf_val, str):
                    uf_val = uf_val.strip().upper()
                    if len(uf_val) > 2:
                        uf_val = uf_val[:2]
                else:
                    uf_val = None

                # Extract tipo_porto from tags
                tipo_porto = props.get('port') or props.get('harbour') or props.get('industrial') or 'port'
                if isinstance(tipo_porto, str):
                    tipo_porto = tipo_porto.strip().lower()
                
                nome_porto = props.get('name') or props.get('operator') or ''
                if isinstance(nome_porto, str):
                    nome_porto = nome_porto.strip()

                data_to_insert.append({
                    "osm_id": osm_id,
                    "nome_porto": nome_porto,
                    "tipo_porto": tipo_porto,
                    "uf": uf_val,
                    "geom_wkt": geom_wkt
                })
            
    logging.info(f"Successfully extracted {len(data_to_insert)} port features.")
    transformed_file = os.path.join(work_dir, "transformed_ports.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f)
        
    return transformed_file

def load_osm_ports(**kwargs) -> None:
    """
    Task 2: Load
    Reads the transformed JSON, creates temporary table, and inserts/updates data into PostGIS.
    """
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='extract_and_transform_ports')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (d["osm_id"], d["nome_porto"], d["tipo_porto"], d["uf"], d["geom_wkt"]) 
        for d in data
    ]
    
    if not data_to_insert:
        logging.warning("No valid port features found to insert. Skipping database operations.")
        return
        
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Creating temporary table for loading...")
    cursor.execute("""
        CREATE TEMP TABLE temp_osm_portos (
            osm_id BIGINT,
            nome_porto VARCHAR(255),
            tipo_porto VARCHAR(100),
            uf CHAR(2),
            geom_wkt TEXT
        ) ON COMMIT DROP;
    """)
    
    sql_insert_temp = """
        INSERT INTO temp_osm_portos (osm_id, nome_porto, tipo_porto, uf, geom_wkt)
        VALUES (%s, %s, %s, %s, %s)
    """
    logging.info(f"Upserting {len(data_to_insert)} records into the temporary table...")
    execute_batch(cursor, sql_insert_temp, data_to_insert)
    
    logging.info("Upserting data into main table from temporary table...")
    cursor.execute("""
        INSERT INTO mesa_a.vetor_osm_portos (osm_id, nome_porto, tipo_porto, uf, geom)
        SELECT DISTINCT ON (osm_id) 
            osm_id, 
            nome_porto, 
            tipo_porto, 
            uf, 
            ST_PointOnSurface(ST_SetSRID(ST_GeomFromText(geom_wkt), 4674))
        FROM temp_osm_portos
        ORDER BY osm_id
        ON CONFLICT (osm_id) DO UPDATE SET
            nome_porto = EXCLUDED.nome_porto,
            tipo_porto = EXCLUDED.tipo_porto,
            uf = EXCLUDED.uf,
            geom = EXCLUDED.geom;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded OSM ports into the database!")
    
    # Cleanup
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_osm_ports",
    start_date=datetime(2024, 1, 1),
    schedule=[osm_dataset], # Runs automatically when the PBF file is updated
    catchup=False,
    tags=["geodata", "osm", "ports"]
) as dag:
    
    check_dependency_task = PythonOperator(
        task_id="check_geofabrik_dependency",
        python_callable=check_pbf_exists
    )
    
    extract_transform_task = PythonOperator(
        task_id="extract_and_transform_ports",
        python_callable=extract_and_transform_ports
    )
    
    load_task = PythonOperator(
        task_id="load_osm_ports",
        python_callable=load_osm_ports
    )
    
    check_dependency_task >> extract_transform_task >> load_task
