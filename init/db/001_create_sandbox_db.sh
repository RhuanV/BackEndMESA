#!/bin/bash
set -e

# Creates the isolated sandbox database used when APP_ENV=sandbox and enables
# PostGIS in it, mirroring the main database so assessments/shapefiles work with
# the same spatial features. Runs only on first cluster initialization.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE ${SANDBOX_DB_NAME};
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${SANDBOX_DB_NAME}" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL
