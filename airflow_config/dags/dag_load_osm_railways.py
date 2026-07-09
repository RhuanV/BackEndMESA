"""
Extracts railways from OpenStreetMap (Geofabrik PBF) via Osmium and loads them into mesa_a.vetor_osm_ferrovias.
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
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

osm_dataset = Dataset("file:///opt/airflow/data/brazil-latest.osm.pbf")

def check_pbf_exists() -> None:
    """Checks whether the PBF file already exists (Geofabrik DAG dependency)."""
    pbf_path = "/opt/airflow/data/brazil-latest.osm.pbf"
    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"Brazil PBF dependency missing at {pbf_path}. Run 'download_geofabrik_data' DAG first.")
    logging.info(f"Dependency met: PBF file found at {pbf_path}.")

def extract_and_transform_railways(**kwargs) -> str:
    """Extract and Transform: filters railways from the PBF and exports them to a processed JSON."""
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_osm_railways_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    pbf_path = "/opt/airflow/data/brazil-latest.osm.pbf"
    filtered_pbf = os.path.join(work_dir, "railways_filtered.osm.pbf")
    geojson_path = os.path.join(work_dir, "railways.geojson")
    
    osmium_bin = shutil.which("osmium")
    if not osmium_bin:
        raise RuntimeError("Executable 'osmium' not found. Verify the installation of 'osmium-tool' in the Dockerfile and ensure the image was rebuilt (--build).")

    logging.info("Filtering features using osmium tags-filter...")
    # Matches way["railway"] and relation["route"~"train|subway|tram|light_rail"]
    subprocess.run([
        osmium_bin, "tags-filter", pbf_path, 
        "w/railway", "r/route=train,subway,tram,light_rail",
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
        
        railway = props.get('railway')
        route = props.get('route')
        
        # Consider only features that directly match the query intent
        if not railway and route not in ['train', 'subway', 'tram', 'light_rail']:
            continue

        # Prefer the 'railway' tag, falling back to 'route'
        railway_val = railway if railway else route

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
                data_to_insert.append({
                    "osm_id": osm_id,
                    "name": props.get('name', ''),
                    "railway": railway_val,
                    "geom_wkt": geom_wkt
                })
            
    logging.info(f"Successfully extracted {len(data_to_insert)} railway features.")
    transformed_file = os.path.join(work_dir, "transformed_railways.json")
    
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f)
        
    return transformed_file

def load_osm_railways(**kwargs) -> None:
    """Load: reads the transformed JSON and upserts the data into PostGIS via a temporary table."""
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='extract_and_transform_railways')
    
    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    data_to_insert = [
        (d["osm_id"], d["name"], d["railway"], d["geom_wkt"]) 
        for d in data
    ]
    
    if not data_to_insert:
        logging.warning("No valid railway features found to insert.")
        return
        
    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    logging.info("Creating temporary table for loading...")
    cursor.execute("""
        CREATE TEMP TABLE temp_osm_railways (
            osm_id BIGINT,
            nome VARCHAR(255),
            tipo_ferrovia VARCHAR(50),
            geom_wkt TEXT
        ) ON COMMIT DROP;
    """)
    
    sql_insert_temp = """
        INSERT INTO temp_osm_railways (osm_id, nome, tipo_ferrovia, geom_wkt)
        VALUES (%s, %s, %s, %s)
    """
    logging.info(f"Upserting {len(data_to_insert)} records into the temporary table...")
    execute_batch(cursor, sql_insert_temp, data_to_insert)
    
    logging.info("Upserting data into main table from temporary table...")
    cursor.execute("""
        INSERT INTO mesa_a.vetor_osm_ferrovias (osm_id, nome, tipo_ferrovia, geom)
        SELECT DISTINCT ON (osm_id) osm_id, nome, tipo_ferrovia, ST_SetSRID(ST_GeomFromText(geom_wkt), 4674)
        FROM temp_osm_railways
        ORDER BY osm_id
        ON CONFLICT (osm_id) DO UPDATE SET
            nome = EXCLUDED.nome,
            tipo_ferrovia = EXCLUDED.tipo_ferrovia,
            geom = EXCLUDED.geom;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Successfully loaded OSM railways into the database!")
    
    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")

with DAG(
    dag_id="load_osm_railways",
    start_date=datetime(2024, 1, 1),
    schedule=[osm_dataset],  # Runs automatically when the PBF is updated
    catchup=False,
    tags=["geodata", "osm", "railways"]
) as dag:
    
    check_dependency_task = PythonOperator(
        task_id="check_geofabrik_dependency",
        python_callable=check_pbf_exists
    )
    
    extract_transform_task = PythonOperator(
        task_id="extract_and_transform_railways",
        python_callable=extract_and_transform_railways
    )
    
    load_task = PythonOperator(
        task_id="load_osm_railways",
        python_callable=load_osm_railways
    )
    
    check_dependency_task >> extract_transform_task >> load_task