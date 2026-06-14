# GeoAvia - Backend MESA-Auto

Backend for the GeoAvia project (SAC/ANAC/ITA partnership) for automating the MESA methodology in airport site prospecting.

## Overview

Current stack:

- Python 3.12
- FastAPI
- PostgreSQL with PostGIS
- Apache Airflow (for ETL and data pipelines)
- Docker and Docker Compose
- Raw SQL with psycopg2 (no ORM)

Current API state:

- User registration with password hashing
- Login with JWT
- Route protection using Bearer token on GET /usuarios
- User management by ID (update username and delete)

## Architecture

Layered architecture:

- API Layer: backend/src/geoavia_backend/main.py
- Service Layer: backend/src/geoavia_backend/service.py
- Repository Layer: backend/src/geoavia_backend/repository.py
- Environment configuration: backend/src/geoavia_backend/database.py
- Data Pipelines (ETL): airflow_config/dags/

Principles:

- Business rules in the service layer
- Data access in the repository using explicit SQL
- Automated spatial data ingestion via Airflow DAGs
- Sensitive variables managed through .env

## Repository Structure

```text
BackEndMESA/
|-- airflow_config/
|   |-- dags/
|   |   |-- dag_load_municipalities.py
|   |   `-- dag_load_states.py
|   |-- plugins/
|   |   `-- config_urls.py
|   |-- Dockerfile
|   `-- requirements.txt
|-- backend/
|   |-- migrations/
|   |   |-- 01_create_tables.sql
|   |   `-- 02_insert_data.sql
|   |-- src/
|   |   `-- geoavia_backend/
|   |       |-- main.py
|   |       |-- service.py
|   |       |-- repository.py
|   |       `-- database.py
|   `-- requirements.txt
|-- .github/
|   `-- copilot-instructions.md
|-- .pre-commit-config.yaml
|-- docker-compose.yml
|-- Dockerfile
`-- README.md
```

## Configurations

There is a .env_example file in the root directory, based on which one may create
one's own .env file.


Notes:

- When running locally outside Docker, use DB_HOST=localhost.
- SECRET_KEY must be unique per environment and should not be versioned.

## How to Run

### Option A: Docker (recommended)
Copie o template de ambiente:
```bash
Copy-Item .env_example .env
```
Edite o arquivo .env:

mantenha DB_HOST=db para Docker
configure DB_USER, DB_PASS, DB_NAME
defina SECRET_KEY forte

Suba o ambiente:
```bash
docker-compose up --build
```

Expected services:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Airflow: http://127.0.0.1:8080 (User: admin / Pass: admin)
- Database: Ports are configured in .env file

#### Accessing the Database via DBeaver

To inspect the tables and run geographic queries, configure a new PostgreSQL connection in DBeaver (or your preferred DB client) with the following parameters (based on your `.env` defaults):
- **Host:** `localhost`
- **Port:** `5433` (or the value of `DB_EXT_PORT`)
- **Database:** `geoavia_main_db` (or the value of `DB_NAME`)
- **Username:** `postgres` (or the value of `DB_USER`)
- **Password:** `123` (or the value of `DB_PASS`)

### Option B: Local Package Installation (Editable Mode)

For development, you may install the backend as a local Python package in **editable mode**.

This allows Python to recognize the project as a proper package and automatically reflect code changes without reinstalling dependencies.

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install the backend in editable mode:

```bash
pip install -e .
```

Run the API:

```bash
uvicorn geoavia_backend.main:app --reload
```

#### Advantages of Editable Installation

- **Proper package resolution:** The module `geoavia_backend` becomes globally available inside the environment.
- **Cleaner imports:** You avoid relative import issues when the project grows.
- **Better IDE support:** Tools like VSCode/Pylance can resolve modules more reliably.
- **No reinstall needed:** Code changes are immediately reflected without reinstalling the package.

## Current Endpoints

Authentication:

- POST /usuarios/signup
- POST /login

Users:

- GET /usuarios (protected with token)
- PUT /usuarios/{user_id}/username
- DELETE /usuarios/{user_id}

## Authentication Flow

- Create a user with POST /usuarios/signup
- Authenticate with POST /login
- Receive access_token
- Send Authorization: Bearer <token> when calling GET /usuarios

## Colaboration Guidelines

Practical suggestions to evolve the repository as a team:

1. Separate the security module
    - Create backend/security.py to centralize hashing, token generation, and validation.
    - Keep backend/service.py focused on business logic.
2. Standardize request/response models
    - Create backend/schemas.py with Pydantic classes for signup, login, and responses.
    - Reduce loose parameters in route definitions.
3. Separate runtime and development dependencies
    - Keep runtime dependencies in requirements.txt.
    - Create requirements-dev.txt for tools like pre-commit and commitizen.
4. Add automated tests
    - tests/unit for service layer tests.
    - tests/integration for routes and authentication.
5. Define collaboration conventions
    - Branch pattern: feat/, fix/, chore/.
    - Pull requests with a minimum checklist (local testing, API impact, database migration).
    - Semantic commits using commitizen (already supported by .pre-commit-config.yaml).
6. Version architectural decisions
    - Create a docs/adr folder to document decisions about security, database, and API design.

## Security

- Passwords must never be stored in plain text.
- Do not commit .env files containing real credentials.
- In production, rotate SECRET_KEY and use secure environment variables.

## Internal References

- Implementation guidelines: .github/copilot-instructions.md
- API entry point: backend/src/geoavia_backend/main.py

## Testing

### Airflow Test Suite

Our Airflow data pipelines are covered by a comprehensive, automated test suite built with `pytest`. These tests ensure that our orchestration logic, DAG integrity, and task execution are highly robust and resilient.

To run the entire Airflow test suite at once, execute the following script from the root directory:

```bash
./run_airflow_tests.sh
```


The test suite is divided into the following key modules:

- DAG Integrity (test_dags_integrity.py): Dynamically loads all DAGs in the dags/ folder to check for Python syntax errors, missing imports, and circular dependencies. It guarantees that no DAG silently fails during the parsing phase.

- Database Connection (test_db_connection.py): Verifies that the Airflow environment can successfully establish a connection to the main GeoAvia PostgreSQL database (geoavia_main_conn), validating authentication and query execution via the PostgresHook.

- Environment Initialization (test_initialization.py): Parses the init_airflow.sh script and asserts against the Airflow metadata database to ensure that the required bootstrap DAGs are automatically unpaused and triggered when the environment starts.

- Scheduler & Triggers (test_scheduler.py): Simulates the passage of time to validate that Airflow's scheduling engine correctly infers data intervals and creates DagRun records for both CRON-scheduled and Dataset-triggered DAGs.

- Task Execution Isolation (test_task_execution.py): Dynamically discovers all tasks across the project (Check, Extract, Transform, Load) and executes their Python logic in complete isolation. It uses extensive mocking (unittest.mock) to simulate network requests, subprocesses (like the osmium tool), file I/O, and database operations. This allows for fast and safe unit testing without modifying the real database or downloading large datasets.

- Failure Handling & Recovery (test_failure_handling.py): Uses an in-memory dummy DAG to simulate real-world operational failures. It validates that Airflow correctly updates task states (up_for_retry, failed, upstream_failed), respects retry 0delays, maintains DagRun consistency, and supports safe manual reprocessing (task clearing).
