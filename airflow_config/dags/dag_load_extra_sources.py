"""Ingestion DAGs for the remaining BDG vetorial sources (Fase 4).

One DAG per still-missing source (INCRA quilombolas/assentamentos, MMA florestas
públicas, CPRM geodiversidade, IBGE biomas), each built from a shared factory
that uses the generic shapefile → (properties JSONB, geom) loader. This keeps
the ingestion robust (no hardcoded per-source attribute names) and DRY.

Note: SICAR sub-layers (APP, Reserva Legal, Rios, Nascentes, Vegetação nativa,
Lagos, Banhados, Área de pousio) follow the existing per-state SICAR DAG
(dag_load_gov_sicar.py) pattern and are added the same way.
"""
import os
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
sys.path.insert(0, plugins_dir)

import config_urls  # noqa: E402
from generic_vetor_ingest import ingest_zip_to_table  # noqa: E402

# (dag_id, table, config_urls attribute, tags)
_SOURCES = [
    ("load_incra_quilombolas", "vetor_incra_quilombolas", "INCRA_QUILOMBOLAS_URL",
     ["geodata", "incra", "quilombolas"]),
    ("load_incra_assentamentos", "vetor_incra_assentamentos", "INCRA_ASSENTAMENTOS_URL",
     ["geodata", "incra", "assentamentos"]),
    ("load_mma_florestas_publicas", "vetor_mma_florestas_publicas", "MMA_FLORESTAS_PUBLICAS_URL",
     ["geodata", "mma", "florestas"]),
    ("load_cprm_geodiversidade", "vetor_cprm_geodiversidade", "CPRM_GEODIVERSIDADE_URL",
     ["geodata", "cprm", "geodiversidade"]),
    ("load_ibge_biomas", "vetor_ibge_biomas", "IBGE_BIOMAS_URL",
     ["geodata", "ibge", "biomas"]),
]


def _make_callable(table: str, url_attr: str):
    def _run(**kwargs):
        url = getattr(config_urls, url_attr)
        if not url:
            raise ValueError(
                f"URL for {table} is not configured. Set {url_attr} in the environment."
            )
        ingest_zip_to_table(url, table, kwargs["run_id"])

    return _run


# Airflow discovers each DAG object in module globals.
for dag_id, table, url_attr, tags in _SOURCES:
    with DAG(
        dag_id=dag_id,
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=tags,
    ) as dag:
        PythonOperator(task_id="ingest", python_callable=_make_callable(table, url_attr))
    globals()[dag_id] = dag
