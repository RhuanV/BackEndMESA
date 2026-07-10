# Database — GeoAvia

## Single source of migrations: Alembic

The application schema is managed **exclusively by Alembic**
(`backend/alembic/versions/`). At boot, the `backend` service runs
`alembic upgrade head` (see [docker-compose.yml](../../docker-compose.yml)).

Do **not** create/edit standalone SQL to change the schema — add an Alembic revision instead.

## Postgres bootstrap

`init/db/` contains only the script run once by the
Postgres container on first startup (it creates the Airflow database). It is mounted at
`/docker-entrypoint-initdb.d` by `docker-compose.yml`. It is not a schema migration.

## Contents of this folder (`docs/database/`)

- `modelagem/` — reference material for the data model. Documentation only, not executed
  by anything:
  - `modelo_conceitual_bd.png` — the conceptual data model diagram.
  - `metadados_vetoriais.csv` — the vector-layer data dictionary (source metadata).
