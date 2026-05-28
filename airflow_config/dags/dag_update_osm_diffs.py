"""
Incremental OSM update DAG using Geofabrik replication diffs.
"""

import os
import logging
import subprocess
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset

DATA_DIR = "/opt/airflow/data"
osm_dataset = Dataset("file:///opt/airflow/data/brazil-latest.osm.pbf")

import sys
plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.insert(0, plugins_dir)

from config_urls import GEODIFF_URL

def update_osm_diffs(**kwargs):

    pbf_path = os.path.join(DATA_DIR, "brazil-latest.osm.pbf")

    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"Arquivo base não encontrado: {pbf_path}. Execute a DAG de download primeiro.")
        
    logging.info(f"Atualizando {pbf_path} de forma incremental a partir de {GEODIFF_URL}...")
    
    # O pyosmium-up-to-date descobre a data do PBF automaticamente, baixa os diffs e os aplica.
    cmd = [
        "pyosmium-up-to-date",
        pbf_path,
        "--ignore-osmosis-headers",
        "--server", GEODIFF_URL,
        "--size", "10000" # Aumentamos o limite para garantir que baixe tudo de uma vez
    ]
    
    # Executamos o comando capturando os logs do terminal para descobrir o motivo exato
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        logging.info(f"STDOUT: {result.stdout.strip()}")
    if result.stderr:
        logging.warning(f"STDERR: {result.stderr.strip()}")
        
    if result.returncode == 0:
        logging.info("Atualização incremental concluída com sucesso!")
    elif result.returncode == 1:
        # pyosmium-up-to-date retorna 1 em caso de limite de tamanho atingido ou PBF mais novo que o servidor
        logging.warning("O pyosmium retornou código 1. Isso pode indicar uma atualização parcial ou que seu arquivo PBF já é tão recente que o servidor ainda não gerou atualizações para ele.")
    elif result.returncode == 3:
        logging.info("O arquivo PBF já está totalmente atualizado. Nenhuma nova atualização foi encontrada.")
    else:
        raise RuntimeError(f"O pyosmium-up-to-date falhou com código {result.returncode}.")


with DAG(
    dag_id="update_osm_diffs",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["osm", "incremental", "geofabrik"]
) as dag:

    update_task = PythonOperator(
        task_id="update_osm_diffs",
        python_callable=update_osm_diffs,
        outlets=[osm_dataset]
    )
