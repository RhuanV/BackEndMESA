# Advanced usage — GeoAvia

Everything beyond the two-command Quick Start in the [README](../README.md): alternative
run modes, database migrations, the full API reference, the RBAC matrix, and extended
troubleshooting.

## Node.js via nvm

Instead of the distribution packages, you can manage Node versions with nvm:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts && nvm use --lts
```

## Alternative run modes

### Docker only (backend, database and Airflow, no frontend)

```bash
docker compose up -d            # cached images
docker compose up --build -d    # force a rebuild after changing requirements/Dockerfile
```

### Force a rebuild with the startup script

`./start.sh` uses cached Docker images by default. Pass `--build` (or `-b`) to rebuild
after changing `requirements.txt` or a `Dockerfile`:

```bash
./start.sh --build
```

### Local backend (editable install, outside Docker)

For backend-only development against a reachable PostgreSQL/PostGIS instance (set
`DB_HOST=localhost`):

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ./backend             # editable install (reads backend/requirements.txt)
uvicorn geoavia_backend.main:app --reload
```

## Accessing the database via DBeaver

Configure a PostgreSQL connection using your `.env` values:

- **Host:** `localhost`
- **Port:** `5433` (or `DB_EXT_PORT`)
- **Database:** `geoavia_main_db` (or `DB_NAME`)
- **Username:** `postgres` (or `DB_USER`)
- **Password:** the value of `DB_PASS`

## Database migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/) for incremental migrations.
Every time the backend container starts it runs `alembic upgrade head` automatically,
applying pending migrations before Uvicorn accepts connections. Alembic never re-runs an
applied migration.

```bash
# Inspect state
docker compose exec backend alembic current   # applied revision
docker compose exec backend alembic history   # full history

# Create a new migration
docker compose exec backend alembic revision -m "describe what this migration does"

# Apply / roll back
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1
```

Fill in `upgrade()` / `downgrade()` using raw SQL via `op.execute(text(...))`:

```python
from alembic import op
from sqlalchemy import text

def upgrade() -> None:
    op.execute(text("ALTER TABLE assessments ADD COLUMN reviewed_at TIMESTAMPTZ;"))

def downgrade() -> None:
    op.execute(text("ALTER TABLE assessments DROP COLUMN IF EXISTS reviewed_at;"))
```

Revision files live in `backend/alembic/versions/` and follow the `NNNN_slug.py`
convention. See [docs/database/README.md](database/README.md).

## API reference

All routers are assembled in `backend/src/geoavia_backend/main.py`. "Auth" = requires a
Bearer token; "Roles" = additional `require_roles` gate. Interactive docs at
`http://localhost:8000/docs`.

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
| POST | `/password-reset` | — | public (admin-issued recovery code) |
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

### Authentication flow

1. Create a user with `POST /users/signup` (requires an authorized caller).
2. Authenticate with `POST /login` (OAuth2 password form: `username` + `password`).
3. Receive `{ "access_token": "<JWT>", "token_type": "bearer" }` (30-minute expiry).
4. Send `Authorization: Bearer <token>` on protected routes.

Token validation and role checks live in `core/auth.py`; tokens are signed with
`SECRET_KEY` using `ALGORITHM` (HS256).

### Password recovery

There is no email/SMTP integration. An **administrador** generates a single-use recovery
code via `POST /users/{user_id}/recovery-code` and relays it out-of-band (only its hash is
stored; it expires in ~30 minutes). The user opens **"Esqueci minha senha"** on the login
page and submits their username + the code + a new password (`POST /password-reset`).

## Access control (RBAC)

Three roles, defined once in `backend/src/geoavia_backend/core/roles.py` and constrained
in the database. See [ADR 0004](adr/0004-rbac-three-roles-and-sandbox.md).

| Role | Description |
| :--- | :--- |
| **operador** | View maps/layers, run analyses, create assessments, view results, export, screening, upload shapefiles. No user management, no admin config, no developer tools. |
| **administrador** | Everything an operador does, plus user management (create/update/delete users, issue recovery codes), layer/source configuration and audit. No developer tools. |
| **desenvolvedor** | Everything, including developer tools — but sandboxed by `APP_ENV`: in `production` the role is read-only and its writes are audited/blocked; in `sandbox` it has full write access. Bound to `DEV_USER`; cannot be renamed or deleted. |

The signup endpoint can assign `{ operador, administrador }`. Granting the privileged
`desenvolvedor` role is restricted to another `desenvolvedor`.

### Frontend page gating (`frontend/src/app/Router.tsx`)

- `/dashboard/map` — all roles
- `/dashboard/analysis`, `/assessment`, `/results`, `/export`, `/screening`,
  `/data/shapefiles` — operador, administrador, desenvolvedor
- `/dashboard/admin/users`, `/admin/layers`, `/admin/audit` — administrador, desenvolvedor
- `/dashboard/dev/health`, `/dev/logs`, `/dev/debug` — desenvolvedor

## Backend tests

```bash
docker compose exec backend pytest
```

See [docs/TESTING.md](TESTING.md) for the full testing guide (Airflow suite, frontend,
manual E2E).

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `start.sh` exits: "Neither .env nor .env_example found" | Missing environment file | Run `cp .env_example .env` (or `bash install.sh`) in the repo root |
| "permission denied while trying to connect to the Docker daemon" | User not in the `docker` group | `sudo usermod -aG docker $USER` then log out/in (or run with `sudo`) |
| "address already in use" on 8000 / 8080 / 5173 / 5433 | Port already taken | Change the matching `*_PORT` in `.env`, or free it: `lsof -i :<port>` → kill the PID |
| `start.sh` hangs on "Waiting for backend health" then times out | Backend crashed or failed migrations | `docker compose logs backend` — usually an Alembic error or the DB not healthy yet |
| Backend logs show `psycopg2.OperationalError` / "connection refused" | DB not healthy or credentials mismatch | Check `docker compose logs db`; ensure `DB_*` match. Full reset: `docker compose down -v && docker compose up` |
| Alembic: "no current revision" on an existing DB | Old schema not tracked by Alembic | `start.sh` auto-runs `alembic stamp head`; otherwise run it manually in the backend container |
| OSM DAGs fail: `FileNotFoundError: .../brazil-latest.osm.pbf` | Base OSM extract not downloaded | In the Airflow UI, trigger the `download_geofabrik_data` DAG first (~1–1.5 GB), then the `load_osm_*` DAGs |
| Airflow tasks fail writing to `/opt/airflow/data` (permission denied) | Volume not owned by the Airflow UID (50000) | The `permission-fixer` service fixes this on startup; if needed: `docker exec geoavia_permission_fixer chown -R 50000:0 /opt/airflow/data` |
| Frontend: blank page / cannot reach the API | Backend not up or wrong `API_PORT` | Ensure the backend is healthy; the Vite proxy (`frontend/vite.config.ts`) targets the API port. Check the browser console |
| `npm install` not run / `node_modules` missing | Fresh checkout | `start.sh` installs automatically; otherwise run `npm install` in `frontend/` |
| A `desenvolvedor` user gets 403 on every write | `APP_ENV=production` makes the developer role read-only | Use an `administrador` account for writes, or set `APP_ENV=sandbox` in a non-production environment |
