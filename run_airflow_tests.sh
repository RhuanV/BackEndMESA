#!/usr/bin/env bash
# ===========================================================
# GeoAvia MESA — Airflow Test Suite Runner
# ===========================================================
set -euo pipefail

echo -e "\033[0;36m╔════════════════════════════════════════════════════════╗\033[0m"
echo -e "\033[0;36m║           Running Airflow Automated Tests              ║\033[0m"
echo -e "\033[0;36m╚════════════════════════════════════════════════════════╝\033[0m"
echo ""

# Check if the Airflow container is running
if ! docker ps | grep -q geoavia_airflow; then
    echo -e "\033[0;31mError: The container 'geoavia_airflow' is not running.\033[0m"
    echo "Please start the environment first with: ./start.sh or docker compose up -d"
    exit 1
fi

echo "Executing pytest inside the geoavia_airflow container..."
echo ""

docker exec -it geoavia_airflow pytest /opt/airflow/tests/airflow/ -v