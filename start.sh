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

# Detect the Compose command once (V2 plugin preferred, fallback to legacy).
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  DC="docker-compose"
fi

MAX_RETRIES=30

# Captures the last `compose up` output for post-mortem diagnostics (port binds, etc.).
COMPOSE_UP_LOG="$(mktemp)"

# Bring the stack up. Idempotent; --remove-orphans clears leftovers from prior runs.
# Tolerant to a non-zero exit (e.g. airflow-init failing) so the health check below can
# diagnose and self-heal instead of aborting the whole script under `set -e`.
start_stack() {
  $DC up $FORCE_BUILD -d --remove-orphans > "$COMPOSE_UP_LOG" 2>&1 || true
  tail -5 "$COMPOSE_UP_LOG"
}

# Poll the backend /health endpoint.
# Returns: 0 = healthy | 1 = generic timeout | 2 = stale-network (name resolution) failure
wait_for_backend() {
  local retry=0
  until curl -sf "http://localhost:${API_PORT}/health" > /dev/null 2>&1; do
    # Fast-fail: containers can't resolve the 'db' service name — the Docker network is
    # in a corrupted state (common on WSL2 after the daemon restarts with containers up).
    if $DC logs backend airflow-init 2>/dev/null | grep -q "Temporary failure in name resolution"; then
      return 2
    fi
    retry=$((retry + 1))
    if [ "$retry" -ge "$MAX_RETRIES" ]; then
      return 1
    fi
    sleep 1
    printf "  Retry %d/%d...\r" "$retry" "$MAX_RETRIES"
  done
  return 0
}

# --- Step 2: Start Docker ---
echo ""
echo -e "${YELLOW}[2/4]${NC} Starting Docker services..."
cd "$ROOT_DIR"

# Read ports from .env (needed by the health check below).
API_PORT=$(grep -E '^API_PORT=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "8000")
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT=$(grep -E '^FRONTEND_PORT=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "5173")
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

start_stack
echo -e "  ${GREEN}✓${NC} Docker services started"

# --- Step 3: Wait for Backend (self-heals a stale Docker network once) ---
echo ""
echo -e "${YELLOW}[3/4]${NC} Waiting for backend health..."
HEALTH_RC=0
wait_for_backend || HEALTH_RC=$?

if [ "$HEALTH_RC" -eq 2 ]; then
  echo -e "  ${YELLOW}⚠ Stale Docker network detected (service 'db' not resolvable).${NC}"
  echo -e "  ${YELLOW}Recreating the network and retrying once...${NC}"
  $DC down --remove-orphans || true   # never -v: preserves the data volumes
  start_stack
  HEALTH_RC=0
  wait_for_backend || HEALTH_RC=$?
fi

if [ "$HEALTH_RC" -eq 0 ]; then
  echo -e "  ${GREEN}✓${NC} Backend is healthy (port ${API_PORT})"
else
  echo -e "  ${RED}✗ Backend did not become healthy${NC}"
  if grep -q "address already in use" "$COMPOSE_UP_LOG" 2>/dev/null; then
    echo -e "  ${YELLOW}A host port is already in use (see the message above).${NC}"
    echo -e "  ${YELLOW}Free the port or change the matching *_PORT in .env. If a previous run${NC}"
    echo -e "  ${YELLOW}left orphaned docker-proxy processes, restart the Docker daemon:${NC}"
    echo -e "  ${YELLOW}  sudo snap restart docker      # or, on Windows: wsl --shutdown${NC}"
  fi
  echo -e "  ${YELLOW}Tip: Check logs with '${DC} logs backend'${NC}"
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
  already_at_head) echo -e "  ${GREEN}✓${NC} Alembic already at head" ;;
  stamped)         echo -e "  ${GREEN}✓${NC} Alembic: existing database stamped as head" ;;
  *)               echo -e "  ${GREEN}✓${NC} Alembic managed by the backend" ;;
esac

# --- Step 3.6: Bootstrap the environment's single user ---
# The database starts empty (no demo seeds). Production bootstraps one admin
# (role administrador); sandbox bootstraps one dev (role desenvolvedor). The
# bootstrap calls UserService directly inside the container (bypassing the
# role-gated signup endpoint) and is idempotent.
APP_ENV=$(grep -E '^APP_ENV=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "production")
APP_ENV="${APP_ENV:-production}"

if [ "$(echo "$APP_ENV" | tr '[:upper:]' '[:lower:]')" = "sandbox" ]; then
  BOOT_USER=$(grep -E '^DEV_USER=' "$ROOT_DIR/.env" | cut -d= -f2); BOOT_USER="${BOOT_USER:-dev}"
  BOOT_PASS=$(grep -E '^DEV_PASS=' "$ROOT_DIR/.env" | cut -d= -f2); BOOT_PASS="${BOOT_PASS:-Dev@12345}"
  BOOT_ROLE=$(grep -E '^DEV_ROLE=' "$ROOT_DIR/.env" | cut -d= -f2); BOOT_ROLE="${BOOT_ROLE:-desenvolvedor}"
else
  BOOT_USER=$(grep -E '^ADMIN_USER=' "$ROOT_DIR/.env" | cut -d= -f2); BOOT_USER="${BOOT_USER:-admin}"
  BOOT_PASS=$(grep -E '^ADMIN_PASS=' "$ROOT_DIR/.env" | cut -d= -f2); BOOT_PASS="${BOOT_PASS:-Admin@1234}"
  BOOT_ROLE=$(grep -E '^ADMIN_ROLE=' "$ROOT_DIR/.env" | cut -d= -f2); BOOT_ROLE="${BOOT_ROLE:-administrador}"
fi

BOOTSTRAP_RESULT=$(docker exec -i geoavia_backend python - <<PY 2>/dev/null || echo "error"
from geoavia_backend.repositories.user import UserRepository
from geoavia_backend.services.user import UserService

if UserRepository().obtain_user_from_username("${BOOT_USER}") is None:
    UserService().register_user("${BOOT_USER}", "${BOOT_PASS}", "${BOOT_ROLE}")
    print("created")
else:
    print("exists")
PY
)

case "$BOOTSTRAP_RESULT" in
  created)
    echo -e "  ${GREEN}✓${NC} Bootstrap user created (${BOOT_USER}/${BOOT_PASS}, role: ${BOOT_ROLE}, env: ${APP_ENV})"
    ;;
  exists)
    echo -e "  ${GREEN}✓${NC} Bootstrap user already exists (${BOOT_USER}, env: ${APP_ENV})"
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
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

npm run dev
