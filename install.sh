#!/usr/bin/env bash
# ===========================================================
# GeoAvia — From-Scratch Installation Script
#
# Prepares the entire monorepo on a clean machine in one command:
# 1. Checks prerequisites (docker, docker compose, node/npm)
# 2. Creates .env from .env_example if missing
# 3. Builds the backend and Airflow images (installs each service's Python deps)
# 4. Installs the frontend dependencies
#
# After it finishes, run `bash start.sh` to bring the stack up.
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
echo -e "${CYAN}║     GeoAvia — Installation Script    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# --- Step 1: Check prerequisites ---
echo -e "${YELLOW}[1/4]${NC} Checking prerequisites..."
MISSING=0

if command -v docker >/dev/null 2>&1; then
  echo -e "  ${GREEN}✓${NC} docker"
else
  echo -e "  ${RED}✗ docker not found — install Docker first${NC}"
  MISSING=1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
  echo -e "  ${GREEN}✓${NC} docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
  echo -e "  ${GREEN}✓${NC} docker-compose"
else
  echo -e "  ${RED}✗ docker compose not found${NC}"
  MISSING=1
fi

if command -v npm >/dev/null 2>&1; then
  echo -e "  ${GREEN}✓${NC} npm"
else
  echo -e "  ${RED}✗ npm not found — install Node.js first${NC}"
  MISSING=1
fi

if [ "$MISSING" -ne 0 ]; then
  echo -e "${RED}Missing prerequisites. Please install them and re-run.${NC}"
  exit 1
fi

# --- Step 2: Create .env ---
echo ""
echo -e "${YELLOW}[2/4]${NC} Checking environment file..."
if [ ! -f "$ROOT_DIR/.env" ]; then
  if [ -f "$ROOT_DIR/.env_example" ]; then
    cp "$ROOT_DIR/.env_example" "$ROOT_DIR/.env"
    echo -e "  ${GREEN}✓${NC} Created .env from .env_example"
    # Generate a strong SECRET_KEY so a fresh install never ships the placeholder.
    SECRET_KEY_VALUE="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY_VALUE}|" "$ROOT_DIR/.env"
    echo -e "  ${GREEN}✓${NC} Generated a strong SECRET_KEY"
    echo -e "  ${RED}⚠ Review .env and set the remaining secrets before production!${NC}"
  else
    echo -e "  ${RED}✗ No .env or .env_example found. Cannot continue.${NC}"
    exit 1
  fi
else
  echo -e "  ${GREEN}✓${NC} .env already exists"
fi

# --- Step 3: Build Docker images (installs backend + Airflow Python deps) ---
echo ""
echo -e "${YELLOW}[3/4]${NC} Building Docker images (backend + Airflow)..."
cd "$ROOT_DIR"
$COMPOSE build
echo -e "  ${GREEN}✓${NC} Images built"

# --- Step 4: Install frontend dependencies ---
echo ""
echo -e "${YELLOW}[4/4]${NC} Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm install
echo -e "  ${GREEN}✓${NC} Frontend dependencies installed"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation complete!            ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC} Next step: ${CYAN}bash start.sh${NC}                 ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
