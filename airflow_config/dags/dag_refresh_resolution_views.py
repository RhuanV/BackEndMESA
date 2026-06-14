"""
DAGs to refresh PostGIS materialized views after each source table is loaded.

Sprint 4 HU-25: cada base table dispara o refresh somente das suas próprias
resolution views.

Two DAGs in this file because Airflow Dataset schedules are AND semantics —
a single DAG with `schedule=[ds_a, ds_b]` would wait for BOTH datasets to
update before running. Splitting them gives OR semantics naturally.

Notification on success/failure goes to the task log via DAG-level callbacks.
"""
import logging
from datetime import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Same URIs as in dag_load_states.py / dag_load_municipalities.py.
# Datasets are matched by URI string; importing isn't required.
states_dataset = Dataset("postgres://geoavia_main_db/state_boundaries")
municipalities_dataset = Dataset("postgres://geoavia_main_db/municipality_boundaries")

STATE_VIEWS = [
    "state_boundaries_z1",
    "state_boundaries_z2",
    "state_boundaries_z3",
]

MUNICIPALITY_VIEWS = [
    "municipality_boundaries_z1",
    "municipality_boundaries_z2",
    "municipality_boundaries_z3",
]


def refresh_views(views: list[str]) -> None:
    """Runs REFRESH MATERIALIZED VIEW for each view, sequentially.

    Non-concurrent: simpler and acceptable for current data sizes. `CONCURRENTLY`
    would require a UNIQUE INDEX on each view, which we don't have yet.
    """
    hook = PostgresHook(postgres_conn_id="geoavia_main_conn")
    conn = hook.get_conn()
    cursor = conn.cursor()

    refreshed = []
    try:
        for view_name in views:
            logging.info(f"Refreshing materialized view: {view_name}")
            cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name};")
            refreshed.append(view_name)
        conn.commit()
        logging.info(f"Successfully refreshed {len(refreshed)} views: {refreshed}")
    finally:
        cursor.close()
        conn.close()


def notify_success(context: dict) -> None:
    dag_run = context.get("dag_run")
    run_id = dag_run.run_id if dag_run else "unknown"
    dag_id = dag_run.dag_id if dag_run else "unknown"
    logging.info(f"[{dag_id}] SUCCESS — run_id={run_id}")


def notify_failure(context: dict) -> None:
    dag_run = context.get("dag_run")
    task = context.get("task_instance")
    exc = context.get("exception")
    dag_id = dag_run.dag_id if dag_run else "unknown"
    run_id = dag_run.run_id if dag_run else "unknown"
    task_id = task.task_id if task else "unknown"
    logging.error(
        f"[{dag_id}] FAILURE — run_id={run_id}, task={task_id}, exception={exc}"
    )


# ============================================================================
# DAG 1 — refresh das views de estado quando state_boundaries é atualizada
# ============================================================================

with DAG(
    dag_id="refresh_state_resolution_views",
    start_date=datetime(2024, 1, 1),
    schedule=[states_dataset],
    catchup=False,
    on_success_callback=notify_success,
    on_failure_callback=notify_failure,
    tags=["geodata", "resolution", "refresh", "states"],
) as dag_states:

    PythonOperator(
        task_id="refresh_state_views",
        python_callable=lambda: refresh_views(STATE_VIEWS),
    )


# ============================================================================
# DAG 2 — refresh das views de município quando municipality_boundaries é atualizada
# ============================================================================

with DAG(
    dag_id="refresh_municipality_resolution_views",
    start_date=datetime(2024, 1, 1),
    schedule=[municipalities_dataset],
    catchup=False,
    on_success_callback=notify_success,
    on_failure_callback=notify_failure,
    tags=["geodata", "resolution", "refresh", "municipalities"],
) as dag_municipalities:

    PythonOperator(
        task_id="refresh_municipality_views",
        python_callable=lambda: refresh_views(MUNICIPALITY_VIEWS),
    )
