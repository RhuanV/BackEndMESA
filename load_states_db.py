"""
Script to load state boundaries from a Shapefile into the PostGIS database.
This script is intended to be run locally for testing purposes before migrating the logic to an Airflow DAG.
"""
import os
import geopandas as gpd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def main() -> None:
    """
    Main function to read the shapefile, process the geometries into WKT,
    and insert them into the state_boundaries table using psycopg2.
    """
    # 1. Read the Shapefile
    print("Loading Shapefile...")
    file_path = "data/BR_UF_2025/BR_UF_2025.shp"
    gdf = gpd.read_file(file_path)
    
    # 2. Prepare the data (extract only what matters and convert geometry to WKT)
    print("Preparing data...")
    data_to_insert = []
    for _, row in gdf.iterrows():
        data_to_insert.append((
            row['CD_UF'],
            row['NM_UF'],
            row['SIGLA_UF'],
            row['geometry'].wkt  # Transform polygon into Well-Known Text (WKT)
        ))

    # 3. Connect to the Database (using port 5433 for external access to Docker)
    print("Connecting to the database...")
    conn = psycopg2.connect(
        host="localhost", # Connecting to localhost since we are running outside docker
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port="5433" 
    )
    cursor = conn.cursor()

    # 4. Clear the table (to ensure idempotency) and Insert
    print("Clearing old data and inserting new data...")
    cursor.execute("TRUNCATE TABLE state_boundaries RESTART IDENTITY;")
    
    sql_insert = """
        INSERT INTO state_boundaries (ibge_code, state_name, state_abbr, geom)
        VALUES (%s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4674)))
    """
    
    execute_batch(cursor, sql_insert, data_to_insert)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Load finished successfully!")

if __name__ == "__main__":
    main()