"""
Loads airports (ANAC CSV) into the mesa_a.vetor_gov_aeroportos table.
"""
import os
import logging
import subprocess
import json
import shutil
import re
import pandas as pd
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_batch

import sys
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

# NOTE ON THE URLS:
# The gov.br portal uses Cloudflare bot-detection that blocks Python requests.
# Extraction shells out to curl with browser headers to work around this.
# Primary URL: registry of public civil airfields (regulated-entities page).
# Fallback URL: open data V1.
ANAC_AEROPORTOS_URLS = [
    "https://www.gov.br/anac/pt-br/assuntos/regulados/aerodromos/cadastro-de-aerodromos/aerodromos-cadastrados/cadastro-de-aerodromos-civis-publicos.csv",
    "https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/aerodromos/aerodromos-publicos/lista-de-aerodromos-publicos-1/aerodromospublicosv1.csv",
]

CURL_HEADERS = [
    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "-H", "Accept-Language: pt-BR,pt;q=0.9,en;q=0.8",
    "-H", "Accept-Encoding: gzip, deflate, br",
    "-H", "Referer: https://www.gov.br/anac/pt-br/",
]


def _download_with_curl(url: str, dest_path: str) -> bool:
    """Downloads the URL via curl with browser headers to work around Cloudflare bot-detection."""
    cmd = ["curl", "-L", "--silent", "--fail", "--compressed",
           "--max-time", "60", "-o", dest_path, "-w", "%{http_code}",
           ] + CURL_HEADERS + [url]

    result = subprocess.run(cmd, capture_output=True, text=True)
    http_code = result.stdout.strip()
    logging.info(f"curl HTTP status: {http_code} for {url}")

    if result.returncode != 0 or not http_code.startswith("2"):
        logging.warning(f"curl failed (exit={result.returncode}, HTTP={http_code}): {result.stderr[:300]}")
        return False

    # Reject HTML error pages that come disguised as a CSV
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        with open(dest_path, "rb") as f:
            head = f.read(512).lower()
        if b"<html" in head or b"<!doctype" in head or b"javascript" in head:
            logging.warning(f"Downloaded file looks like an HTML page, not a CSV. Rejecting.")
            os.remove(dest_path)
            return False
        return True

    return False


def extract_aeroportos(**kwargs) -> str:
    """Extract: downloads the ANAC CSV, trying the candidate URLs in order."""
    run_id = kwargs['run_id'].replace(":", "_").replace("-", "_")
    work_dir = f"/tmp/geoavia_gov_aeroportos_{run_id}"
    os.makedirs(work_dir, exist_ok=True)
    csv_path = os.path.join(work_dir, "aeroportos.csv")

    for url in ANAC_AEROPORTOS_URLS:
        logging.info(f"Attempting download from: {url}")
        if _download_with_curl(url, csv_path):
            logging.info(f"Successfully downloaded CSV ({os.path.getsize(csv_path)} bytes) from {url}")
            return csv_path
        logging.warning(f"Failed to download from {url}, trying next...")

    raise RuntimeError(
        "All ANAC URL candidates failed. The portal may be temporarily unavailable "
        "or the URLs may have changed. Check: "
        "https://www.gov.br/anac/pt-br/assuntos/regulados/aerodromos/cadastro-de-aerodromos/aerodromos-cadastrados"
    )


def dms_to_decimal(dms_str: str) -> float | None:
    """Converts a DMS coordinate (e.g. "25° 31' 54'' S") to decimal degrees; negative for S and O/W, None if unreadable."""
    if not dms_str or (isinstance(dms_str, float)):
        return None
    s = str(dms_str).strip().replace(",", ".")
    # Already in decimal form?
    try:
        val = float(s)
        return val
    except ValueError:
        pass
    pattern = r"(\d+)\s*[°º]\s*(\d+)\s*['']\s*([\d.]+)\s*[\"'']{0,2}\s*([NSEWOnsewо]?)"
    m = re.search(pattern, s)
    if not m:
        return None
    deg = float(m.group(1))
    mins = float(m.group(2))
    secs = float(m.group(3))
    direction = m.group(4).upper()
    decimal = deg + mins / 60 + secs / 3600
    if direction in ("S", "O", "W"):
        decimal = -decimal
    return decimal


def transform_aeroportos(**kwargs) -> str:
    """Transform: reads the CSV, extracts lat/lon and relevant fields and builds the WKT Point geometry."""
    ti = kwargs['ti']
    csv_path = ti.xcom_pull(task_ids='extract_aeroportos')

    logging.info(f"Reading CSV: {csv_path}")
    df = None
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        for sep in (';', ','):
            try:
                candidate = pd.read_csv(csv_path, encoding=enc, sep=sep, skiprows=1, header=0, dtype=str)
                if len(candidate.columns) > 4:
                    df = candidate
                    logging.info(f"Parsed with encoding={enc}, sep='{sep}'")
                    break
            except Exception as exc:
                logging.debug(f"Failed to read CSV with encoding={enc}, sep='{sep}': {exc}")
                continue
        if df is not None:
            break

    if df is None:
        raise ValueError("Could not parse the downloaded CSV with any known encoding/separator combination.")

    df.columns = [c.strip().lower() for c in df.columns]
    logging.info(f"Columns: {list(df.columns)}")
    logging.info(f"Rows: {len(df)}")

    lat_col = next((c for c in df.columns if 'lat' in c), None)
    lon_col = next((c for c in df.columns if 'lon' in c or 'lng' in c), None)

    if not lat_col or not lon_col:
        raise ValueError(f"Cannot identify lat/lon columns. Available: {list(df.columns)}")

    logging.info(f"Using lat='{lat_col}', lon='{lon_col}'")

    def clean(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        s = str(v).strip()
        return s if s and s.lower() not in ('nan', 'none', '-') else None

    data_to_insert = []
    skipped = 0
    for _, row in df.iterrows():
        lat = dms_to_decimal(row.get(lat_col))
        lon = dms_to_decimal(row.get(lon_col))

        if lat is None or lon is None or (lat == 0.0 and lon == 0.0):
            skipped += 1
            continue

        nome = clean(row.get('nome'))
        municipio = clean(
            row.get('município atendido') or row.get('municipio atendido') or
            row.get('município') or row.get('municipio')
        )
        uf = clean(row.get('uf'))
        codigo_iata = clean(row.get('iata') or row.get('código iata') or row.get('codigo iata'))
        codigo_icao = clean(
            row.get('código oaci') or row.get('codigo oaci') or
            row.get('ciad') or row.get('oaci')
        )
        tipo = clean(row.get('operação') or row.get('operacao') or row.get('tipo'))

        data_to_insert.append({
            "nome": nome,
            "municipio": municipio,
            "uf": uf,
            "codigo_iata": codigo_iata,
            "codigo_icao": codigo_icao,
            "tipo": tipo,
            "geom_wkt": f"POINT({lon} {lat})"
        })

    logging.info(f"Transformed {len(data_to_insert)} airports with valid coordinates ({skipped} skipped)")

    work_dir = os.path.dirname(csv_path)
    transformed_file = os.path.join(work_dir, "transformed_aeroportos.json")
    with open(transformed_file, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f, ensure_ascii=False)

    return transformed_file


def load_aeroportos(**kwargs) -> None:
    """Load: inserts the data into PostGIS and cleans up temporary files."""
    ti = kwargs['ti']
    transformed_file = ti.xcom_pull(task_ids='transform_aeroportos')

    with open(transformed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_to_insert = [
        (d["nome"], d["municipio"], d["uf"], d["codigo_iata"], d["codigo_icao"], d["tipo"], d["geom_wkt"])
        for d in data
    ]

    logging.info("Connecting to database via Airflow Connection...")
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()

    logging.info("Truncating table and inserting new records...")
    cursor.execute("TRUNCATE TABLE mesa_a.vetor_gov_aeroportos RESTART IDENTITY;")

    sql_insert = """
        INSERT INTO mesa_a.vetor_gov_aeroportos (nome, municipio, uf, codigo_iata, codigo_icao, tipo, geom)
        VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4674))
    """
    execute_batch(cursor, sql_insert, data_to_insert)
    conn.commit()
    cursor.close()
    conn.close()
    logging.info(f"Successfully loaded {len(data_to_insert)} government airports into the database!")

    work_dir = os.path.dirname(transformed_file)
    shutil.rmtree(work_dir, ignore_errors=True)
    logging.info(f"Cleaned up temporary directory: {work_dir}")


with DAG(
    dag_id="load_gov_aeroportos",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["geodata", "anac", "aeroportos"]
) as dag:

    extract_task = PythonOperator(task_id="extract_aeroportos", python_callable=extract_aeroportos)
    transform_task = PythonOperator(task_id="transform_aeroportos", python_callable=transform_aeroportos)
    load_task = PythonOperator(task_id="load_aeroportos", python_callable=load_aeroportos)

    extract_task >> transform_task >> load_task