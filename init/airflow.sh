#!/bin/bash
set -e

echo "1. Migrating Airflow Database..."
airflow db migrate

echo "2. Creating Airflow Admin User..."
airflow users create --username "${AIRFLOW_USER:-admin}" --password "${AIRFLOW_PASS:-admin}" --firstname admin --lastname admin --role Admin --email admin@email.com || true

echo "3. Unpausing and triggering DAGs..."

# Load States DAG
airflow dags unpause load_state_boundaries || true
airflow dags trigger load_state_boundaries || true

# Load Municipalities DAG
airflow dags unpause load_municipality_boundaries || true
airflow dags trigger load_municipality_boundaries || true