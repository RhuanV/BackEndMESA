#!/usr/bin/env bash
# ===========================================================
# GeoAvia — startup script
#
# Chooses the environment (sandbox or production), prepares the
# stack and leaves a ready-to-use login printed at the end.
#
# Usage:
#   ./start.sh              -> ask for the environment (menu)
#   ./start.sh sandbox      -> test environment (isolated database)
#   ./start.sh prod         -> real environment (production)
#   ./start.sh --no-build   -> do not rebuild the Docker images
#   ./start.sh -h           -> help
# ===========================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# Build is enabled by default; the Docker cache keeps it fast when nothing changed.
DO_BUILD=1
ENV_ARG=""

for arg in "$@"; do
  case "$arg" in
    sandbox|SANDBOX)            ENV_ARG="sandbox" ;;
    prod|production|PROD)       ENV_ARG="production" ;;
    -b|--build)                 DO_BUILD=1 ;;
    --no-build)                 DO_BUILD=0 ;;
    -h|--help)
      echo "Usage: ./start.sh [sandbox|prod] [--no-build]"
      echo "  sandbox    isolated test environment (own database)"
      echo "  prod       real environment (main database)"
      echo "  --no-build do not rebuild the Docker images"
      exit 0 ;;
    *) echo -e "${YELLOW}Ignored argument: $arg${NC}" ;;
  esac
done

BUILD_FLAG=""; [ "$DO_BUILD" -eq 1 ] && BUILD_FLAG="--build"

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     GeoAvia — MESA-Auto Framework    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# --- Prerequisites ---
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}x Docker is not installed.${NC}"
  echo -e "  Install Docker Desktop (Windows/Mac) or Docker Engine (Linux) and run again."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}x Docker is installed but not running.${NC}"
  echo -e "  Start Docker Desktop (or the service) and run this script again."
  exit 1
fi

# Detect the Compose command (prefer V2, fall back to the legacy binary).
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

# --- .env ---
echo -e "${YELLOW}[1/5]${NC} Checking configuration (.env)..."
if [ ! -f "$ROOT_DIR/.env" ]; then
  if [ -f "$ROOT_DIR/.env_example" ]; then
    cp "$ROOT_DIR/.env_example" "$ROOT_DIR/.env"
    echo -e "  ${GREEN}ok${NC} .env created from .env_example"
    echo -e "  ${YELLOW}! Review .env and set strong passwords before any real deployment.${NC}"
  else
    echo -e "  ${RED}x Neither .env nor .env_example found. Cannot start.${NC}"
    exit 1
  fi
else
  echo -e "  ${GREEN}ok${NC} .env found"
fi

# Read a value from .env (first match); prints empty if absent.
env_get() { grep -E "^$1=" "$ROOT_DIR/.env" 2>/dev/null | head -n1 | cut -d= -f2- || true; }

# Write/update a key in .env idempotently.
env_set() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ROOT_DIR/.env"; then
    # Use | as the separator so values containing / do not break the substitution.
    sed -i "s|^${key}=.*|${key}=${val}|" "$ROOT_DIR/.env"
  else
    printf '\n%s=%s\n' "$key" "$val" >> "$ROOT_DIR/.env"
  fi
}

CURRENT_ENV="$(echo "$(env_get APP_ENV)" | tr '[:upper:]' '[:lower:]')"
[ -z "$CURRENT_ENV" ] && CURRENT_ENV="sandbox"

# Ensure a strong JWT signing key: the backend refuses to boot in production
# with the placeholder. Generate one if missing/placeholder so it "just works".
CURRENT_SECRET="$(env_get SECRET_KEY)"
if [ -z "$CURRENT_SECRET" ] || [ "$CURRENT_SECRET" = "change_for_a_strong_password" ]; then
  if command -v python3 >/dev/null 2>&1; then
    env_set SECRET_KEY "$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    echo -e "  ${GREEN}ok${NC} strong SECRET_KEY generated in .env"
  else
    echo -e "  ${YELLOW}! Set a strong SECRET_KEY in .env (python3 not found to generate one).${NC}"
  fi
fi

# --- Environment choice ---
echo ""
echo -e "${YELLOW}[2/5]${NC} Choosing the environment..."
APP_ENV=""
if [ -n "$ENV_ARG" ]; then
  APP_ENV="$ENV_ARG"
elif [ -t 0 ]; then
  echo -e "  Which environment do you want to run?"
  echo -e "    ${CYAN}1)${NC} Sandbox    — TEST environment, own database (experiment freely)"
  echo -e "    ${CYAN}2)${NC} Production — REAL environment, main database"
  default_choice=2; [ "$CURRENT_ENV" = "sandbox" ] && default_choice=1
  read -r -p "  Type 1 or 2 [default: ${default_choice}]: " choice || true
  choice="${choice:-$default_choice}"
  case "$choice" in
    1) APP_ENV="sandbox" ;;
    2) APP_ENV="production" ;;
    *) echo -e "  ${YELLOW}Invalid option; using the default.${NC}"
       [ "$default_choice" = "1" ] && APP_ENV="sandbox" || APP_ENV="production" ;;
  esac
else
  # No terminal and no argument: keep whatever is in .env.
  APP_ENV="$CURRENT_ENV"
fi

env_set APP_ENV "$APP_ENV"
if [ "$APP_ENV" = "sandbox" ]; then
  echo -e "  ${GREEN}ok${NC} Environment: ${CYAN}SANDBOX${NC} (tests)"
else
  echo -e "  ${GREEN}ok${NC} Environment: ${CYAN}PRODUCTION${NC}"
fi

# Ports and DB credentials (for the health check and sandbox database creation).
API_PORT="$(env_get API_PORT)"; API_PORT="${API_PORT:-8000}"
AIRFLOW_PORT="$(env_get AIRFLOW_PORT)"; AIRFLOW_PORT="${AIRFLOW_PORT:-8080}"
FRONTEND_PORT="$(env_get FRONTEND_PORT)"; FRONTEND_PORT="${FRONTEND_PORT:-5173}"
AIRFLOW_PORT="$(env_get AIRFLOW_PORT)"; AIRFLOW_PORT="${AIRFLOW_PORT:-8080}"
DB_USER="$(env_get DB_USER)"; DB_USER="${DB_USER:-postgres}"
DB_NAME="$(env_get DB_NAME)"; DB_NAME="${DB_NAME:-geoavia_main_db}"
SANDBOX_DB_NAME="$(env_get SANDBOX_DB_NAME)"; SANDBOX_DB_NAME="${SANDBOX_DB_NAME:-geoavia_sandbox_db}"

cd "$ROOT_DIR"
COMPOSE_UP_LOG="$(mktemp)"
trap 'rm -f "$COMPOSE_UP_LOG"' EXIT
MAX_RETRIES=40

wait_for_backend() {
  local retry=0
  until curl -sf "http://localhost:${API_PORT}/health" >/dev/null 2>&1; do
    if $DC logs backend airflow-init 2>/dev/null | grep -q "Temporary failure in name resolution"; then
      return 2
    fi
    retry=$((retry + 1)); [ "$retry" -ge "$MAX_RETRIES" ] && return 1
    sleep 1; printf "  Attempt %d/%d...\r" "$retry" "$MAX_RETRIES"
  done
  return 0
}

# --- Database: bring Postgres up first and ensure the environment database exists ---
echo ""
echo -e "${YELLOW}[3/5]${NC} Preparing the database..."
$DC up $BUILD_FLAG -d db > "$COMPOSE_UP_LOG" 2>&1 || { tail -8 "$COMPOSE_UP_LOG"; echo -e "  ${RED}x Failed to start the database.${NC}"; exit 1; }

# Wait for Postgres to accept connections.
db_retry=0
until $DC exec -T db pg_isready -U "$DB_USER" >/dev/null 2>&1; do
  db_retry=$((db_retry + 1)); [ "$db_retry" -ge "$MAX_RETRIES" ] && { echo -e "  ${RED}x Database did not become ready.${NC}"; break; }
  sleep 1; printf "  Waiting for the database %d/%d...\r" "$db_retry" "$MAX_RETRIES"
done
echo -e "  ${GREEN}ok${NC} Database ready            "

# In sandbox, make sure the isolated database exists (with PostGIS).
if [ "$APP_ENV" = "sandbox" ]; then
  if ! $DC exec -T db psql -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='${SANDBOX_DB_NAME}'" 2>/dev/null | grep -q 1; then
    $DC exec -T db psql -U "$DB_USER" -c "CREATE DATABASE ${SANDBOX_DB_NAME};" >/dev/null 2>&1 || true
    $DC exec -T db psql -U "$DB_USER" -d "${SANDBOX_DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS postgis;" >/dev/null 2>&1 || true
    echo -e "  ${GREEN}ok${NC} Sandbox database created (${SANDBOX_DB_NAME})"
  else
    echo -e "  ${GREEN}ok${NC} Sandbox database already exists (${SANDBOX_DB_NAME})"
  fi
fi

# --- Bring up the rest and recreate the backend so it re-reads APP_ENV ---
echo ""
echo -e "${YELLOW}[4/5]${NC} Starting the services (${APP_ENV})..."
$DC up $BUILD_FLAG -d --remove-orphans >> "$COMPOSE_UP_LOG" 2>&1 || true
# The backend reads APP_ENV at boot: recreate only it to pick up the chosen environment.
$DC up -d --force-recreate --no-deps backend >> "$COMPOSE_UP_LOG" 2>&1 || true
tail -3 "$COMPOSE_UP_LOG"

HEALTH_RC=0; wait_for_backend || HEALTH_RC=$?
if [ "$HEALTH_RC" -eq 2 ]; then
  echo -e "  ${YELLOW}! Unstable Docker network (service 'db' not resolved). Recreating once...${NC}"
  $DC down --remove-orphans || true   # never -v: preserve the data
  $DC up $BUILD_FLAG -d --remove-orphans >> "$COMPOSE_UP_LOG" 2>&1 || true
  HEALTH_RC=0; wait_for_backend || HEALTH_RC=$?
fi

if [ "$HEALTH_RC" -eq 0 ]; then
  echo -e "  ${GREEN}ok${NC} Backend healthy (port ${API_PORT})     "
else
  echo -e "  ${RED}x The backend did not become healthy.${NC}"
  if grep -q "address already in use" "$COMPOSE_UP_LOG" 2>/dev/null; then
    echo -e "  ${YELLOW}A port is already in use. Free it or change the *_PORT in .env.${NC}"
  fi
  echo -e "  ${YELLOW}Tip: check the logs with '${DC} logs backend'${NC}"
fi

# Alembic stamp guard (old installs with pre-Alembic tables).
$DC exec -T backend bash -c "
  alembic current 2>&1 | grep -qE '(head|\(head\))' ||
  (alembic current 2>&1 | grep -qi 'no current revision' && alembic stamp head 2>&1) || true
" >/dev/null 2>&1 || true

# --- Environment login user: create it or update the password from .env ---
echo ""
echo -e "${YELLOW}[5/5]${NC} Preparing the login user..."
if [ "$APP_ENV" = "sandbox" ]; then
  BOOT_USER="$(env_get DEV_USER)";  BOOT_USER="${BOOT_USER:-dev}"
  BOOT_PASS="$(env_get DEV_PASS)";  BOOT_PASS="${BOOT_PASS:-Dev@12345}"
  BOOT_ROLE="$(env_get DEV_ROLE)";  BOOT_ROLE="${BOOT_ROLE:-desenvolvedor}"
else
  BOOT_USER="$(env_get ADMIN_USER)"; BOOT_USER="${BOOT_USER:-admin}"
  BOOT_PASS="$(env_get ADMIN_PASS)"; BOOT_PASS="${BOOT_PASS:-Admin@1234}"
  BOOT_ROLE="$(env_get ADMIN_ROLE)"; BOOT_ROLE="${BOOT_ROLE:-administrador}"
fi

BOOTSTRAP_RESULT=$(BOOT_USER="$BOOT_USER" BOOT_PASS="$BOOT_PASS" BOOT_ROLE="$BOOT_ROLE" \
  docker exec -i -e BOOT_USER -e BOOT_PASS -e BOOT_ROLE geoavia_backend python - <<'PY' 2>/dev/null || echo "error"
import os
from geoavia_backend.core.passwords import validate_password_strength
from geoavia_backend.repositories.user import UserRepository
from geoavia_backend.services.user import UserService, SecurityService

username = os.environ["BOOT_USER"]
password = os.environ["BOOT_PASS"]
role = os.environ["BOOT_ROLE"]

repo, svc, sec = UserRepository(), UserService(), SecurityService()
user = repo.obtain_user_from_username(username)
if user is None:
    svc.register_user(username, password, role)
    print("created")
else:
    validate_password_strength(password)
    repo.update_password_hash(user["id"], sec.get_password_hash(password))
    print("updated")
PY
)

case "$BOOTSTRAP_RESULT" in
  created) echo -e "  ${GREEN}ok${NC} User created and ready to use" ;;
  updated) echo -e "  ${GREEN}ok${NC} User updated (password from .env applied)" ;;
  *)       echo -e "  ${YELLOW}! Could not prepare the user (${BOOTSTRAP_RESULT}). See '${DC} logs backend'.${NC}" ;;
esac

# --- Frontend ---
echo ""
echo -e "${YELLOW}[extra]${NC} Preparing the frontend..."
cd "$FRONTEND_DIR"
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
  if [ "$NODE_MAJOR" -lt 20 ] 2>/dev/null; then
    echo -e "  ${YELLOW}! Your Node is v$(node -v 2>/dev/null). The frontend needs Node 20+.${NC}"
    echo -e "  ${YELLOW}  Install a 20+ version (e.g. via nvm or fnm) for the panel to open.${NC}"
  fi
else
  echo -e "  ${YELLOW}! Node not found. Install Node 20+ to run the frontend.${NC}"
fi
if [ ! -d "node_modules" ]; then
  echo -e "  Installing frontend dependencies..."
  npm install --silent || echo -e "  ${YELLOW}! Failed to install frontend dependencies.${NC}"
fi

# --- Final panel ---
ENV_LABEL="PRODUCTION"; [ "$APP_ENV" = "sandbox" ] && ENV_LABEL="SANDBOX (tests)"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  GeoAvia is up!                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo -e "  Environment: ${CYAN}${ENV_LABEL}${NC}"
echo -e "  System:      ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  API/Docs:    ${CYAN}http://localhost:${API_PORT}/docs${NC}"
echo -e "  Airflow:     ${CYAN}http://localhost:${AIRFLOW_PORT}${NC}"
echo ""
echo -e "  ${GREEN}Log in with:${NC}"
echo -e "    User:     ${CYAN}${BOOT_USER}${NC}"
echo -e "    Password: ${CYAN}${BOOT_PASS}${NC}"
echo ""
echo -e "  ${YELLOW}New users created by the admin receive a first-access code${NC}"
echo -e "  ${YELLOW}and set their own password from the link on the login screen.${NC}"
echo ""
echo -e "  ${YELLOW}The frontend will start below. Press Ctrl+C to stop.${NC}"
echo ""

npm run dev
