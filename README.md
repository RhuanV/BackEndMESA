# GeoAvia — MESA-Auto

GeoAvia is the platform of the SAC/ANAC/ITA partnership that automates the **MESA**
methodology for airport site prospecting. It is a **monorepo** with three services
orchestrated by Docker Compose:

- **Backend** — FastAPI REST API (Python 3.12)
- **Frontend** — React + TypeScript + Vite (MapLibre GL)
- **Airflow** — ETL/data-ingestion pipelines (Apache Airflow 2.9.3)
- **Database** — PostgreSQL 15 + PostGIS 3.4

## Overview

Stack:

- Python 3.12 · FastAPI · Uvicorn
- PostgreSQL + PostGIS
- Apache Airflow (ETL and spatial data pipelines)
- React 19 · TypeScript · Vite · MapLibre GL
- Docker & Docker Compose V2
- Raw SQL with psycopg2 (no ORM); Alembic for schema migrations

Current capabilities:

- Authentication with JWT and password hashing (bcrypt)
- Role-Based Access Control (RBAC) with 3 roles, enforced on backend and frontend
- Spatial screening of candidate sites (viável / intermediário / restrito)
- Map layer delivery as GeoJSON (with zoom/bbox filtering) and layer source configuration
- User shapefile upload and ingestion (HU-31)
- MESA assessments, weighted analysis, ranking and export
- State/municipality region lookup
- Airflow DAG triggering and audit logging

## Architecture

Layered backend, with absolute imports inside `backend/src/geoavia_backend/`:

- **API layer** — `api/` : one router per domain (assembled in `main.py`)
- **Service layer** — `services/` : business rules
- **Repository layer** — `repositories/` : data access with explicit SQL (psycopg2)
- **Core** — `core/` : cross-cutting concerns (`auth`, `db`, `database`, `roles`, `geo_params`)
- **Schemas** — `schemas/` : Pydantic request/response models
- **Data pipelines (ETL)** — `airflow_config/dags/`

Principles:

- Business rules live in the service layer; data access uses parameterized SQL.
- There is **no ORM**: `core/db.py` opens psycopg2 connections directly. SQLAlchemy is
  only a dependency of the Alembic migration tooling.
- **Alembic is the single source of truth** for the schema (`backend/alembic/versions/`).
- Automated spatial data ingestion runs through Airflow DAGs.
- Sensitive variables are managed through `.env`.

## Repository Structure

```text
Geoavia/
|-- airflow_config/                 # Airflow DAGs, plugins, image
|   |-- dags/
|   |-- plugins/
|   |-- Dockerfile
|   `-- requirements.txt
|-- backend/
|   |-- alembic/                     # schema migrations — the single source of truth
|   |   `-- versions/
|   |-- alembic.ini
|   |-- src/
|   |   `-- geoavia_backend/         # layered package (absolute imports)
|   |       |-- main.py              # app assembly only: CORS + include_router
|   |       |-- api/                 # one router per domain (health, users, layers,
|   |       |                        #   screening, airflow, shapefiles, mesa, regions)
|   |       |-- services/            # business logic (user, layers, screening, ...)
|   |       |-- repositories/        # DB access via explicit SQL (user, layers, ...)
|   |       |-- schemas/             # Pydantic request/response models
|   |       `-- core/                # config & cross-cutting (auth, db, database,
|   |                                #   roles, geo_params)
|   |-- tests/                       # backend pytest suite (app smoke tests)
|   `-- requirements.txt
|-- frontend/
|   `-- src/
|       |-- app/                     # bootstrap, router, guards
|       |-- components/              # shared: ui/, layout/, feedback/ (index.ts barrels)
|       |-- features/                # feature slices (map, auth, assessment, ...)
|       |-- lib/                     # api client, constants, security
|       `-- types/                   # global types (barrel: @/types)
|-- docs/
|   `-- database/                    # DB reference material
|       |-- modelagem/               # conceptual model, reference SQL dumps
|       `-- legacy-migrations/       # pre-Alembic .sql, archived (superseded)
|-- init/                            # container init scripts (centralized)
|   |-- airflow.sh                   # Airflow DB migrate + admin user + DAG unpause
|   `-- db/                          # one-off Postgres init (creates the Airflow DB)
|-- tests/                           # Airflow test suite (mounted into airflow containers)
|   `-- pytest.ini                   # pytest config for the Airflow suite
|-- .pre-commit-config.yaml
|-- docker-compose.yml
|-- Dockerfile                       # backend image
|-- install.sh                       # from-scratch setup (build images + frontend deps)
|-- start.sh                         # bring the stack up
|-- run_airflow_tests.sh             # run the Airflow test suite
`-- README.md
```

The backend package is organized in layers — `api` (routers) → `services` (business
logic) → `repositories` (DB). See [docs/database/README.md](docs/database/README.md) for
the database/migrations layout. The top-level `tests/` folder holds the **Airflow** test
suite; backend unit tests live in `backend/tests/`.

## Configuration (`.env`)

Copy [.env_example](.env_example) to `.env` and adjust as needed. All services read from
this single file.

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `DB_HOST` | Database host (`db` inside Docker, `localhost` for external scripts) | `db` |
| `DB_NAME` | Main application database (FastAPI + PostGIS data) | `geoavia_main_db` |
| `AIRFLOW_DB` | Airflow metadata database name | `geoavia_airflow_db` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASS` | Database password (keep secret in production) | `123` |
| `DB_PORT` | Internal database port (container) | `5432` |
| `DB_EXT_PORT` | External database port exposed to the host | `5433` |
| `API_PORT` | FastAPI backend port | `8000` |
| `AIRFLOW_PORT` | Airflow Web UI port | `8080` |
| `FRONTEND_PORT` | React/Vite dev server port | `5173` |
| `SECRET_KEY` | JWT signing key (unique per environment, do not version) | `change_for_a_strong_password` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `APP_ENV` | `sandbox` = developer role has full write access; otherwise (`production`) the `desenvolvedor` role is read-only and audited | `sandbox` |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins; empty = local frontend only | *(empty)* |
| `AIRFLOW_USER` | Airflow Web UI admin username | `admin` |
| `AIRFLOW_PASS` | Airflow Web UI admin password | `admin` |
| `SHAPEFILE_MAX_UPLOAD_MB` | Max shapefile upload size (MB) | `500` |
| `DEV_USER` | Bootstrap application user (protected, see RBAC) | `admin` |
| `DEV_PASS` | Bootstrap application password | `admin123` |
| `DEV_ROLE` | Bootstrap application role | `desenvolvedor` |
| `VITE_API_BASE_URL` | Frontend API base (proxied by Vite) | `/api` |
| `VITE_MAPLIBRE_STYLE_URL` | Base map style | demotiles |
| `VITE_SATELLITE_STYLE_URL` | Satellite map style | demotiles |
| `VITE_OSM_STYLE_URL` | OpenStreetMap style | demotiles |
| `VITE_IBGE_WMS_URL` | IBGE WMS endpoint | IBGE geoserver |
| `VITE_MAPBIOMAS_WMS_URL` | MapBiomas data source | MapBiomas public |
| `VITE_CPRM_WMS_URL` | CPRM WMS endpoint | CPRM geoserver |

Notes:

- When running the backend locally **outside** Docker, use `DB_HOST=localhost`.
- `SECRET_KEY` must be unique per environment and must never be committed.
- The **Airflow Web UI** login (`AIRFLOW_USER`/`AIRFLOW_PASS`, default `admin`/`admin`) is
  distinct from the **application** login (`DEV_USER`/`DEV_PASS`, default `admin`/`admin123`).

## Prerequisites (Linux/WSL)

You need Docker (with Docker Compose V2) and Node.js.

### 1. Docker & Docker Compose V2

```bash
# Update package lists
sudo apt update

# Install Docker
sudo apt install -y docker.io

# Install Docker Compose V2 plugin (provides `docker compose`)
sudo apt install -y docker-compose-v2

# Optional: run Docker without sudo (log out/in afterwards)
sudo usermod -aG docker $USER
```

### 2. Node.js & NPM (for the frontend)

```bash
# Option A — Ubuntu APT (quick)
sudo apt install -y nodejs npm

# Option B — NVM (recommended for version management)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts && nvm use --lts
```

## From-Scratch Installation

On a clean machine, a single script installs everything (creates `.env`, builds the
backend and Airflow images, installs the frontend dependencies):

```bash
bash install.sh
```

When it finishes, bring the stack up with `bash start.sh`.

## How to Run

### Option A — Unified Monorepo Startup (recommended)

Starts the whole application (Database + Backend + Airflow in Docker, Frontend locally in
Vite dev mode) with one command:

1. Create the environment file (skip if `install.sh` already did it):
   ```bash
   cp .env_example .env
   ```
2. Review `.env` (set a strong `SECRET_KEY`, adjust ports if needed).
3. Start:
   ```bash
   ./start.sh
   ```

> [!TIP]
> `./start.sh` uses cached Docker images by default. To force a rebuild (e.g. after
> changing `requirements.txt` or a `Dockerfile`), pass `--build` (or `-b`):
> ```bash
> ./start.sh --build
> ```

### Option B — Docker Only (Backend, Database & Airflow)

To run the backend services without the frontend:

```bash
docker compose up -d            # cached images
docker compose up --build -d    # force rebuild
```

### Services & URLs

| Service | URL / Port | Credentials |
| :--- | :--- | :--- |
| Frontend | http://localhost:5173 | app login (see below) |
| API | http://localhost:8000 | Bearer token |
| Swagger docs | http://localhost:8000/docs | — |
| Airflow Web UI | http://localhost:8080 | `admin` / `admin` |
| Database | `localhost:5433` (`DB_EXT_PORT`) | `DB_USER` / `DB_PASS` |

Default **application** login (bootstrapped by `start.sh`): `admin` / `admin123`
(`DEV_USER` / `DEV_PASS`).

#### Accessing the database via DBeaver

Configure a PostgreSQL connection (using your `.env` values):

- **Host:** `localhost`
- **Port:** `5433` (or `DB_EXT_PORT`)
- **Database:** `geoavia_main_db` (or `DB_NAME`)
- **Username:** `postgres` (or `DB_USER`)
- **Password:** `123` (or `DB_PASS`)

### Option C — Local Backend (editable install, optional)

For backend-only development outside Docker you can run the API against a reachable
PostgreSQL/PostGIS instance (set `DB_HOST=localhost`):

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ./backend             # editable install (reads backend/requirements.txt)
uvicorn geoavia_backend.main:app --reload
```

## Database Migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/) for incremental migrations.
Every time the backend container starts, it runs `alembic upgrade head` automatically,
applying pending migrations before Uvicorn accepts connections. Migration history is
tracked in the `alembic_version` table; Alembic never re-runs an applied migration.

### Checking the current state

```bash
docker compose exec backend alembic current   # applied revision
docker compose exec backend alembic history   # full history
```

### Creating a new migration

1. Generate the revision file inside the running container:
   ```bash
   docker compose exec backend alembic revision -m "describe what this migration does"
   ```
   This creates a file like `backend/alembic/versions/NNNN_describe_what_this_migration_does.py`.
2. Edit it and fill in `upgrade()` / `downgrade()` using `op.execute(text(...))` with raw SQL:
   ```python
   from alembic import op
   from sqlalchemy import text

   def upgrade() -> None:
       op.execute(text("ALTER TABLE assessments ADD COLUMN reviewed_at TIMESTAMPTZ;"))

   def downgrade() -> None:
       op.execute(text("ALTER TABLE assessments DROP COLUMN IF EXISTS reviewed_at;"))
   ```
3. Apply it (or just restart the backend, which runs `upgrade head` on start):
   ```bash
   docker compose exec backend alembic upgrade head
   ```

### Rolling back one revision

```bash
docker compose exec backend alembic downgrade -1
```

Revision files live in `backend/alembic/versions/` and follow the `NNNN_slug.py`
convention. The pre-Alembic SQL files are archived under
`docs/database/legacy-migrations/` for historical reference and are no longer executed.

## API Endpoints

All routers are assembled in `backend/src/geoavia_backend/main.py`. Paths below are the
full client-facing paths. "Auth" = requires a Bearer token; "Roles" = additional
`require_roles` gate.

| Method | Path | Auth | Roles |
| :--- | :--- | :--- | :--- |
| GET | `/health` | — | — |
| POST | `/login` | — | — |
| GET | `/users` | ✓ | — |
| POST | `/users/signup` | ✓ | administrador, desenvolvedor |
| PUT | `/users/{user_id}/username` | ✓ | administrador, desenvolvedor |
| PUT | `/users/{user_id}/password` | ✓ | DEV_USER only |
| DELETE | `/users/{user_id}` | ✓ | administrador, desenvolvedor |
| POST | `/users/{user_id}/recovery-code` | ✓ | administrador, desenvolvedor |
| POST | `/password-reset` | — | public (uses an admin-issued recovery code) |
| GET | `/layers/{layer_name}` | ✓ | — |
| GET | `/layers/{layer_name}/source` | ✓ | — |
| PUT | `/layers/{layer_name}/source` | ✓ | administrador, desenvolvedor |
| POST | `/screening` | ✓ | operador, administrador, desenvolvedor |
| POST | `/airflow/trigger/{dag_id}` | ✓ | operador, administrador, desenvolvedor |
| GET | `/airflow/triggers` | ✓ | operador, administrador, desenvolvedor |
| POST | `/shapefiles/upload` | ✓ | operador, administrador, desenvolvedor |
| GET | `/shapefiles` | ✓ | operador, administrador, desenvolvedor |
| GET | `/shapefiles/{upload_id}/features` | ✓ | operador, administrador, desenvolvedor |
| POST | `/assessments` | ✓ | — |
| GET | `/assessments` | ✓ | — |
| GET | `/ranking` | ✓ | — |
| POST | `/analysis/run` | ✓ | — |
| GET | `/analysis/status/{job_id}` | ✓ | — |
| GET | `/export/{format}` | ✓ | — |
| GET | `/regions/states` | ✓ | — |
| GET | `/regions/states/{sigla}/municipalities` | ✓ | — |

Interactive documentation is available at http://localhost:8000/docs (Swagger).

## Authentication Flow

1. Create a user with `POST /users/signup` (requires an authorized caller).
2. Authenticate with `POST /login` (OAuth2 password form: `username` + `password`).
3. Receive `{ "access_token": "<JWT>", "token_type": "bearer" }` (30-minute expiry).
4. Send `Authorization: Bearer <token>` on protected routes.

Token validation and role checks live in `core/auth.py` (`obtain_current_user`,
`require_roles`); tokens are signed with `SECRET_KEY` using `ALGORITHM` (HS256).

### Password recovery

There is no email/SMTP integration. An **administrador** generates a single-use
recovery code for a user via `POST /users/{user_id}/recovery-code` and relays it
out-of-band (the code is returned once; only its hash is stored and it expires in
~30 minutes). The user then opens the login page's **"Esqueci minha senha"** and
enters their username + the code + a new password (`POST /password-reset`).

## Access Control (RBAC)

The system enforces RBAC with **3 roles**, defined once in
`backend/src/geoavia_backend/core/roles.py` and constrained in the database
(`alembic/versions/0016_migrate_roles_to_three.py`). See
[ADR 0004](docs/adr/0004-rbac-three-roles-and-sandbox.md).

### 1. Roles

| Role | Description |
| :--- | :--- |
| **operador** | Operates the program: view maps/layers, run analyses, create assessments, view results, export, screening, upload shapefiles. No user management, no admin config, no developer tools. |
| **administrador** | Everything an operador does, **plus** user management (create/update/delete users, issue password-recovery codes), layer/source configuration and audit. No developer tools. |
| **desenvolvedor** | Everything, including developer tools — but **sandboxed** by `APP_ENV`: in `production` the role is read-only and its write attempts are audited/blocked; in `sandbox` it has full write access. Bound to `DEV_USER`; protected (cannot be renamed or deleted). |

> The signup endpoint can assign `{ operador, administrador }`. Granting the
> privileged `desenvolvedor` role is restricted to another `desenvolvedor`.

### 2. Frontend page gating (`frontend/src/app/Router.tsx`)

- `/dashboard/map` — all roles
- `/dashboard/analysis` — operador, administrador, desenvolvedor
- `/dashboard/assessment` — operador, administrador, desenvolvedor
- `/dashboard/results` — operador, administrador, desenvolvedor
- `/dashboard/export` — operador, administrador, desenvolvedor
- `/dashboard/screening` — operador, administrador, desenvolvedor
- `/dashboard/data/shapefiles` — operador, administrador, desenvolvedor
- `/dashboard/admin/users` — administrador, desenvolvedor
- `/dashboard/admin/layers` — administrador, desenvolvedor
- `/dashboard/admin/audit` — administrador, desenvolvedor
- `/dashboard/dev/health` — desenvolvedor
- `/dashboard/dev/logs` — desenvolvedor
- `/dashboard/dev/debug` — desenvolvedor

## Common Errors / Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `start.sh` exits: "No .env or .env_example found" | Missing environment file | Run `cp .env_example .env` (or `bash install.sh`) in the repo root |
| "permission denied while trying to connect to the Docker daemon" | User not in the `docker` group | `sudo usermod -aG docker $USER` then log out/in (or run with `sudo`) |
| "address already in use" on 8000 / 8080 / 5173 / 5433 | Port already taken on the host | Change the matching port in `.env` (`API_PORT`, `AIRFLOW_PORT`, `FRONTEND_PORT`, `DB_EXT_PORT`), or free it: `lsof -i :<port>` → kill the PID |
| `start.sh` hangs on "Waiting for backend health" then times out (30s) | Backend crashed or failed migrations | `docker compose logs backend` — usually an Alembic error or the DB not healthy yet |
| Backend logs show `psycopg2.OperationalError` / "connection refused" | DB not healthy or credentials mismatch | Check `docker compose logs db`; ensure `DB_*` in `.env` match. Full reset: `docker compose down -v && docker compose up` |
| Alembic: "no current revision" on an existing DB | Old schema not tracked by Alembic | `start.sh` auto-runs `alembic stamp head`; otherwise run it manually inside the backend container |
| OSM DAGs fail: `FileNotFoundError: /opt/airflow/data/brazil-latest.osm.pbf` | Base OSM extract not downloaded | In the Airflow UI, unpause and trigger the `download_geofabrik_data` DAG first (downloads ~1–1.5 GB), then run the `load_osm_*` / `update_osm_diffs` DAGs |
| Airflow tasks fail writing to `/opt/airflow/data` (permission denied) | Volume not owned by the Airflow UID (50000) | The `permission-fixer` service fixes this on startup; if needed: `docker exec geoavia_permission_fixer chown -R 50000:0 /opt/airflow/data` |
| `run_airflow_tests.sh`: "The container 'geoavia_airflow' is not running" | Airflow container down | `docker compose up -d`, confirm with `docker ps \| grep geoavia_airflow`, then re-run |
| Frontend: blank page / cannot reach the API | Backend not up or wrong `API_PORT` | Ensure the backend is healthy; the Vite proxy (`frontend/vite.config.ts`) targets the API port. Check the browser console |
| `npm install` not run / `node_modules` missing | Fresh checkout | `start.sh` installs automatically; otherwise run `npm install` in `frontend/` |
| DBeaver/external client cannot connect | Wrong host/port | Use `localhost:5433` (`DB_EXT_PORT`), db `geoavia_main_db`, user `postgres`, password from `DB_PASS` |
| A `desenvolvedor` user gets 403 on every write (POST/PUT/DELETE) | `APP_ENV=production` makes the developer role read-only (sandbox mode) | Use an `administrador` account for writes, or set `APP_ENV=sandbox` in a non-production environment |

## Testing

> Guia completo (automatizados + E2E manual, sandbox vs produção): [docs/TESTING.md](docs/TESTING.md).

### Airflow test suite

The Airflow pipelines are covered by an automated `pytest` suite (DAG integrity, DB
connection, scheduler, initialization, task execution, failure handling). Run it from the
repo root (with the stack up):

```bash
./run_airflow_tests.sh
```

The suite runs clean (**75 passed, 0 warnings**); its configuration lives in
[tests/pytest.ini](tests/pytest.ini). Modules:

- **DAG integrity** (`test_dags_integrity.py`) — loads every DAG to catch syntax errors,
  missing imports and circular dependencies.
- **Database connection** (`test_db_connection.py`) — verifies the Airflow environment can
  reach the main GeoAvia database (`geoavia_main_conn`) via `PostgresHook`.
- **Initialization** (`test_initialization.py`) — parses the init script and asserts the
  bootstrap DAGs are unpaused/triggered on startup.
- **Scheduler & triggers** (`test_scheduler.py`) — validates data-interval inference and
  `DagRun` creation for CRON- and Dataset-triggered DAGs.
- **Task execution isolation** (`test_task_execution.py`) — runs each task's Python logic
  in isolation using mocks for network, subprocess (osmium), file I/O and DB.
- **Failure handling & recovery** (`test_failure_handling.py`) — validates task-state
  transitions (`up_for_retry`, `failed`, `upstream_failed`), retry delays, `DagRun`
  consistency and safe reprocessing.

### Backend tests

```bash
docker compose exec backend pytest
```

## Collaboration Guidelines

- **Branches:** `feat/`, `fix/`, `chore/`.
- **Commits:** semantic commits via commitizen (enforced by
  [.pre-commit-config.yaml](.pre-commit-config.yaml)).
- **Pull requests:** include a short checklist — local testing, API impact, and any
  database migration added.
- **Architecture decisions:** consider documenting significant choices (security,
  database, API design) under `docs/`.

## Security

- Passwords are never stored in plain text (bcrypt hashing).
- Never commit `.env` files with real credentials.
- Rotate `SECRET_KEY` in production and provide it via secure environment variables.

## Internal References

- API entry point: `backend/src/geoavia_backend/main.py`
- Database & migrations: [docs/database/README.md](docs/database/README.md)
