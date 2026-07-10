#!/usr/bin/env bash
# ===========================================================
# GeoAvia — Unified Startup Script
#
# Starts the entire monorepo in one command:
# 1. Validates environment (.env)
# 2. Starts Docker services (DB + Backend + Airflow)
# 3. Waits for backend health
# 4. Installs frontend deps and starts Vite dev server
# ===========================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Default: do not force rebuild
FORCE_BUILD=""

# Parse arguments
for arg in "$@"; do
  case $arg in
    --build|-b)
      FORCE_BUILD="--build"
      shift
      ;;
  esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     GeoAvia — MESA-Auto Framework    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# --- Step 1: Check .env ---
echo -e "${YELLOW}[1/4]${NC} Checking environment..."
if [ ! -f "$ROOT_DIR/.env" ]; then
  if [ -f "$ROOT_DIR/.env_example" ]; then
    cp "$ROOT_DIR/.env_example" "$ROOT_DIR/.env"
    echo -e "  ${GREEN}✓${NC} Created .env from .env_example"
    echo -e "  ${RED}⚠ Please review .env and set your secrets before production!${NC}"
  else
    echo -e "  ${RED}✗ No .env or .env_example found. Cannot start.${NC}"
    exit 1
  fi
else
  echo -e "  ${GREEN}✓${NC} .env found (unified: backend + frontend)"
fi

# --- Step 2: Start Docker ---
echo ""
echo -e "${YELLOW}[2/4]${NC} Starting Docker services..."
cd "$ROOT_DIR"
if docker compose version >/dev/null 2>&1; then
  docker compose up $FORCE_BUILD -d 2>&1 | tail -5
else
  docker-compose up $FORCE_BUILD -d 2>&1 | tail -5
fi
echo -e "  ${GREEN}✓${NC} Docker services started"

# --- Step 3: Wait for Backend ---
echo ""
echo -e "${YELLOW}[3/4]${NC} Waiting for backend health..."
API_PORT=$(grep -E '^API_PORT=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "8000")
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT=$(grep -E '^FRONTEND_PORT=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "5173")
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

MAX_RETRIES=30
RETRY=0
until curl -sf "http://localhost:${API_PORT}/health" > /dev/null 2>&1; do
  RETRY=$((RETRY + 1))
  if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
    echo -e "  ${RED}✗ Backend did not respond after ${MAX_RETRIES}s${NC}"
    echo -e "  ${YELLOW}Tip: Check logs with 'docker compose logs backend'${NC}"
    break
  fi
  sleep 1
  printf "  Retry %d/%d...\r" "$RETRY" "$MAX_RETRIES"
done

if [ "$RETRY" -lt "$MAX_RETRIES" ]; then
  echo -e "  ${GREEN}✓${NC} Backend is healthy (port ${API_PORT})"
fi

# --- Step 3.5: Alembic stamp guard (existing installations) ---
# If the DB already has tables from the old docker-entrypoint-initdb.d system but
# alembic_version doesn't exist yet, stamp it as head so Alembic knows the schema
# is already up to date and won't try to re-run all migrations from scratch.
STAMP_RESULT=$(docker compose exec -T backend bash -c "
  alembic current 2>&1 | grep -qE '(head|\(head\))' && echo 'already_at_head' ||
  (alembic current 2>&1 | grep -qi 'no current revision' &&
   alembic stamp head 2>&1 && echo 'stamped') ||
  echo 'ok'
" 2>/dev/null || echo "skipped")
case "$STAMP_RESULT" in
  already_at_head) echo -e "  ${GREEN}✓${NC} Alembic já está no head" ;;
  stamped)         echo -e "  ${GREEN}✓${NC} Alembic: banco existente marcado como head" ;;
  *)               echo -e "  ${GREEN}✓${NC} Alembic gerenciado pelo backend" ;;
esac

# --- Step 3.6: Bootstrap admin user ---
# Sprint 3: the POST /users/signup endpoint now requires a coordinator/supervisor JWT.
# Since the DB starts without any real users (seeds have placeholder hashes and can't log in),
# the bootstrap is done by calling UserService directly inside the container, bypassing
# the endpoint. Idempotent: checks for existence before creating.
DEV_USER=$(grep -E '^DEV_USER=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "admin")
DEV_USER="${DEV_USER:-admin}"
DEV_PASS=$(grep -E '^DEV_PASS=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "admin123")
DEV_PASS="${DEV_PASS:-admin123}"
DEV_ROLE=$(grep -E '^DEV_ROLE=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "desenvolvedor")
DEV_ROLE="${DEV_ROLE:-desenvolvedor}"

BOOTSTRAP_RESULT=$(docker exec -i geoavia_backend python - <<PY 2>/dev/null || echo "error"
from geoavia_backend.repository import UserRepository
from geoavia_backend.service import UserService

if UserRepository().obtain_user_from_username("${DEV_USER}") is None:
    UserService().register_user("${DEV_USER}", "${DEV_PASS}", "${DEV_ROLE}")
    print("created")
else:
    print("exists")
PY
)

case "$BOOTSTRAP_RESULT" in
  created)
    echo -e "  ${GREEN}✓${NC} Bootstrap user created (${DEV_USER}/${DEV_PASS}, role: ${DEV_ROLE})"
    ;;
  exists)
    echo -e "  ${GREEN}✓${NC} Bootstrap user already exists (${DEV_USER}/${DEV_PASS})"
    ;;
  *)
    echo -e "  ${YELLOW}⚠${NC} Bootstrap failed (${BOOTSTRAP_RESULT}) — login may not work"
    ;;
esac

# --- Step 4: Start Frontend ---
echo ""
echo -e "${YELLOW}[4/4]${NC} Starting frontend dev server..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo -e "  Installing dependencies..."
  npm install --silent
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           GeoAvia is running!            ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Frontend:  ${CYAN}http://localhost:${FRONTEND_PORT}${NC}        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Backend:   ${CYAN}http://localhost:${API_PORT}${NC}        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Swagger:   ${CYAN}http://localhost:${API_PORT}/docs${NC}   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Airflow:   ${CYAN}http://localhost:${AIRFLOW_PORT}${NC}   ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

npm run dev
