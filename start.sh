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
docker compose up --build -d 2>&1 | tail -5
echo -e "  ${GREEN}✓${NC} Docker services started"

# --- Step 3: Wait for Backend ---
echo ""
echo -e "${YELLOW}[3/4]${NC} Waiting for backend health..."
API_PORT=$(grep -E '^API_PORT=' "$ROOT_DIR/.env" | cut -d= -f2 || echo "8000")
API_PORT="${API_PORT:-8000}"

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
echo -e "${GREEN}║${NC}  Frontend:  ${CYAN}http://localhost:5173${NC}        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Backend:   ${CYAN}http://localhost:${API_PORT}${NC}        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Swagger:   ${CYAN}http://localhost:${API_PORT}/docs${NC}   ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

npm run dev
