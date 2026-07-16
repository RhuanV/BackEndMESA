"""Loads the metadata spreadsheet into mesa_a.layer_catalog (RF01).

Idempotent ingestion: parses the vetorial metadata CSV and upserts each row by
``layer_key``, so re-runs never duplicate entries. This keeps the layer
metadata catalog (the GUI metadata viewer's source of truth) in sync with the
spreadsheet without editing code in two places.
"""
import csv
import io
import logging
import os
import sys
import unicodedata
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_batch

plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
sys.path.insert(0, plugins_dir)

# Default CSV location inside the repo (mounted into the Airflow container).
DEFAULT_CSV = os.environ.get(
    "LAYER_CATALOG_CSV",
    "/opt/airflow/docs/database/modelagem/metadados_vetoriais.csv",
)

_COLUMNS = [
    "tema",
    "plano_informacao",
    "data_atualizacao_fonte",
    "periodicidade",
    "fonte",
    "segregacao",
    "datum",
    "epsg",
    "formato",
    "geometria",
    "observacoes",
    "endereco",
]
_EMPTY_TOKENS = {"", "-", "n/a", "não há", "nao ha"}
_LAYER_OVERRIDES = {
    "estado__ibge": {"grupo": "base", "backend_table": "state_boundaries", "available": True},
    "municipio__ibge": {
        "grupo": "base",
        "backend_table": "municipality_boundaries",
        "available": True,
    },
}
_UPSERT_COLUMNS = [
    "layer_key",
    "tema",
    "plano_informacao",
    "fonte",
    "fonte_principal",
    "data_atualizacao_fonte",
    "periodicidade",
    "segregacao",
    "datum",
    "epsg",
    "formato",
    "geometria",
    "observacoes",
    "endereco",
    "grupo",
    "data_type",
    "backend_table",
    "available",
]


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = "".join(c if c.isalnum() else "_" for c in ascii_only)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def _clean(value):
    if value is None:
        return None
    stripped = value.strip()
    return None if stripped.lower() in _EMPTY_TOKENS else stripped


def parse_catalog(**kwargs) -> str:
    """Parse the CSV into JSON-serializable upsert rows (via XCom)."""
    with open(DEFAULT_CSV, encoding="utf-8") as f:
        reader = csv.reader(io.StringIO(f.read()))

    rows = []
    seen_keys = {}
    seen_planos = {}
    for index, raw in enumerate(reader):
        if not raw or all(not (c or "").strip() for c in raw):
            continue
        if index == 0 and (raw[0] or "").strip().upper() == "TEMA":
            continue
        cells = (raw + [None] * len(_COLUMNS))[: len(_COLUMNS)]
        rec = {col: _clean(cells[i]) for i, col in enumerate(_COLUMNS)}
        if not rec["plano_informacao"] and not rec["fonte"]:
            continue

        plano_slug = _slugify(rec["plano_informacao"] or "sem_plano")
        plano_count = seen_planos.get(plano_slug, 0)
        seen_planos[plano_slug] = plano_count + 1
        fonte_principal = plano_count == 0

        base = f"{plano_slug}__{_slugify(rec['fonte'] or 'sem_fonte')}"
        count = seen_keys.get(base, 0)
        seen_keys[base] = count + 1
        layer_key = base if count == 0 else f"{base}_{count + 1}"
        ov = _LAYER_OVERRIDES.get(layer_key, {})

        rows.append(
            {
                "layer_key": layer_key,
                "tema": rec["tema"],
                "plano_informacao": rec["plano_informacao"],
                "fonte": rec["fonte"],
                "fonte_principal": fonte_principal,
                "data_atualizacao_fonte": rec["data_atualizacao_fonte"],
                "periodicidade": rec["periodicidade"],
                "segregacao": rec["segregacao"],
                "datum": rec["datum"],
                "epsg": rec["epsg"],
                "formato": rec["formato"],
                "geometria": rec["geometria"],
                "observacoes": rec["observacoes"],
                "endereco": rec["endereco"],
                "grupo": ov.get("grupo"),
                "data_type": ov.get("data_type", "vector"),
                "backend_table": ov.get("backend_table"),
                "available": ov.get("available", False),
            }
        )
    logging.info("Parsed %d catalog entries from %s", len(rows), DEFAULT_CSV)
    ti = kwargs["ti"]
    ti.xcom_push(key="rows", value=rows)
    return str(len(rows))


def upsert_catalog(**kwargs) -> None:
    ti = kwargs["ti"]
    rows = ti.xcom_pull(task_ids="parse_catalog", key="rows") or []
    if not rows:
        logging.warning("No catalog rows to upsert. Skipping.")
        return

    placeholders = ", ".join(["%s"] * len(_UPSERT_COLUMNS))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in _UPSERT_COLUMNS if c != "layer_key")
    sql = f"""
        INSERT INTO mesa_a.layer_catalog ({", ".join(_UPSERT_COLUMNS)})
        VALUES ({placeholders})
        ON CONFLICT (layer_key) DO UPDATE SET {updates}, updated_at = NOW();
    """
    data = [tuple(r.get(c) for c in _UPSERT_COLUMNS) for r in rows]

    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cur = conn.cursor()
    execute_batch(cur, sql, data)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("Upserted %d rows into mesa_a.layer_catalog", len(data))


with DAG(
    dag_id="load_metadata_catalog",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Runs manually / on demand
    catchup=False,
    tags=["metadata", "catalog", "rf01"],
) as dag:
    parse_task = PythonOperator(task_id="parse_catalog", python_callable=parse_catalog)
    upsert_task = PythonOperator(task_id="upsert_catalog", python_callable=upsert_catalog)

    parse_task >> upsert_task
