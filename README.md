# GeoAvia — MESA-Auto

GeoAvia is the platform of the SAC/ANAC/ITA partnership that automates the **MESA**
methodology for airport site prospecting. It screens candidate sites across Brazil using
weighted spatial analysis over regulatory and geographic layers.

It is a monorepo with four services orchestrated by Docker Compose:

- **Backend** — FastAPI REST API (Python 3.12)
- **Frontend** — React + TypeScript + Vite (MapLibre GL)
- **Airflow** — ETL / spatial-data ingestion pipelines (Apache Airflow 2.9.3)
- **Database** — PostgreSQL 15 + PostGIS 3.4

## Prerequisites

You need three tools installed:

- **Docker** with the **Docker Compose V2** plugin (`docker compose`)
- **Node.js 20+** (for the frontend)
- **Python 3.12** (only used by the helper scripts to generate secrets)

On Ubuntu/Debian/WSL:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 nodejs npm python3
sudo usermod -aG docker $USER   # run Docker without sudo — log out/in afterwards
```

## Quick Start

Two commands bring the whole stack up:

```bash
git clone <repo-url> && cd Geoavia
bash install.sh    # checks prerequisites, creates .env, generates a strong SECRET_KEY, builds images
bash start.sh      # asks for the environment (sandbox/production) and starts everything
```

When `start.sh` finishes it prints the access URLs and a ready-to-use login. Open:

- **System (frontend):** http://localhost:5173
- **API / Swagger docs:** http://localhost:8000/docs
- **Airflow Web UI:** http://localhost:8080

The default application login is printed by `start.sh` (in sandbox: `dev` / `Dev@12345`).
The Airflow UI login defaults to `admin` / `admin`. **Change these before any real
deployment** — see [docs/DEPLOY.md](docs/DEPLOY.md).

## Reference data (boundaries)

The **state boundaries** layer is populated automatically: a migration loads a committed
seed (`backend/seed/state_boundaries.sql.gz`, IBGE BR_UF_2025 mesh) into
`mesa_a.vetor_limites_estaduais`. The **municipality boundaries** are not committed (the
full mesh is too large); load them on demand via the Airflow DAG
`load_municipality_boundaries`.

## Project structure

```text
Geoavia/
├── airflow_config/          # Airflow DAGs, plugins, image
├── backend/
│   ├── alembic/versions/    # schema migrations — the single source of truth
│   ├── src/geoavia_backend/ # layered package: api → services → repositories + core
│   ├── seed/                # committed seed data (state boundaries)
│   └── tests/               # backend pytest suite
├── frontend/src/            # app/, components/, features/, lib/, types/
├── docs/                    # DEPLOY, ADVANCED, TESTING, ADRs, database reference
├── init/                    # container init scripts (Airflow + Postgres bootstrap)
├── tests/                   # Airflow test suite
├── docker-compose.yml
├── install.sh               # from-scratch setup
└── start.sh                 # bring the stack up
```

The backend is layered — `api` (routers) → `services` (business logic) → `repositories`
(data access via explicit, parameterized SQL). There is **no ORM**; Alembic is the single
source of truth for the schema. See the ADRs in [docs/adr/](docs/adr/README.md).

## Configuration

All services read a single `.env` file at the repo root. `install.sh` creates it from
[.env_example](.env_example) and generates a strong `SECRET_KEY`. The variables you are
most likely to touch:

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `APP_ENV` | `sandbox` (developer role has full write) or `production` (developer role read-only) | `sandbox` |
| `SECRET_KEY` | JWT signing key — unique per environment, never commit | *(generated)* |
| `DB_PASS` | Database password | `123` |
| `CORS_ORIGINS` | Comma-separated allowed origins; empty = local frontend only | *(empty)* |
| `AIRFLOW_USER` / `AIRFLOW_PASS` | Airflow Web UI credentials | `admin` / `admin` |

Every variable is documented inline in [.env_example](.env_example).

## Documentation

- **[docs/DEPLOY.md](docs/DEPLOY.md)** — production deployment tutorial (HTTPS, hardening).
- **[docs/ADVANCED.md](docs/ADVANCED.md)** — Docker-only run, local backend dev, DBeaver,
  migrations, the full API reference and RBAC matrix, extended troubleshooting.
- **[docs/TESTING.md](docs/TESTING.md)** — automated tests and manual E2E testing.
- **[docs/adr/](docs/adr/README.md)** — architecture decision records.
- **[docs/database/](docs/database/README.md)** — database and migrations reference.

## Security

- Passwords are hashed with bcrypt and never stored in plain text.
- Authentication uses JWT (OAuth2 bearer tokens); role checks live in `core/auth.py`.
- Never commit `.env`. Rotate `SECRET_KEY`, `DB_PASS`, and the bootstrap passwords before
  going live. In `production` the backend refuses to boot with the placeholder key.

See [docs/DEPLOY.md](docs/DEPLOY.md) for the full production hardening checklist.

## Troubleshooting

| Symptom | Fix |
| :--- | :--- |
| "permission denied ... Docker daemon" | Add your user to the `docker` group: `sudo usermod -aG docker $USER`, then log out/in |
| "address already in use" (8000/8080/5173/5433) | Change the matching `*_PORT` in `.env`, or free the port |
| `start.sh` times out on backend health | Check `docker compose logs backend` — usually an Alembic error or the DB not ready |
| Frontend blank / cannot reach the API | Confirm the backend is healthy; the Vite proxy targets `API_PORT` |
| A `desenvolvedor` user gets 403 on writes | `APP_ENV=production` makes that role read-only — use an `administrador`, or set `APP_ENV=sandbox` |

More cases in [docs/ADVANCED.md](docs/ADVANCED.md#troubleshooting).

## Contributing

- **Branches:** `feat/`, `fix/`, `chore/`.
- **Commits:** semantic commits enforced by [.pre-commit-config.yaml](.pre-commit-config.yaml).
- **Pull requests:** note local testing, API impact, and any database migration added.
- **Architecture decisions:** document significant choices as an ADR under
  [docs/adr/](docs/adr/README.md).
