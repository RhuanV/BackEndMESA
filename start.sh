#!/usr/bin/env bash
# ===========================================================
# GeoAvia — Script de inicialização (fácil para iniciantes)
#
# Pergunta o ambiente (sandbox ou produção), prepara tudo e já
# deixa o usuário de acesso pronto com a senha mostrada no fim.
#
# Uso:
#   ./start.sh              -> pergunta o ambiente (menu)
#   ./start.sh sandbox      -> ambiente de testes (banco próprio)
#   ./start.sh prod         -> ambiente real (produção)
#   ./start.sh --no-build   -> não reconstrói as imagens Docker
#   ./start.sh -h           -> ajuda
# ===========================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Cores
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# Build habilitado por padrão (cache do Docker deixa rápido quando nada muda).
DO_BUILD=1
ENV_ARG=""

for arg in "$@"; do
  case "$arg" in
    sandbox|SANDBOX)            ENV_ARG="sandbox" ;;
    prod|production|PROD)       ENV_ARG="production" ;;
    -b|--build)                 DO_BUILD=1 ;;
    --no-build)                 DO_BUILD=0 ;;
    -h|--help)
      echo "Uso: ./start.sh [sandbox|prod] [--no-build]"
      echo "  sandbox    ambiente de testes isolado (banco próprio)"
      echo "  prod       ambiente real (banco principal)"
      echo "  --no-build não reconstrói as imagens Docker"
      exit 0 ;;
    *) echo -e "${YELLOW}Argumento ignorado: $arg${NC}" ;;
  esac
done

BUILD_FLAG=""; [ "$DO_BUILD" -eq 1 ] && BUILD_FLAG="--build"

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     GeoAvia — MESA-Auto Framework    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# --- Pré-requisitos amigáveis ---
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}✗ Docker não está instalado.${NC}"
  echo -e "  Instale o Docker Desktop (Windows/Mac) ou o Docker Engine (Linux) e rode de novo."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}✗ O Docker está instalado, mas não está rodando.${NC}"
  echo -e "  Abra o Docker Desktop (ou inicie o serviço) e rode este script novamente."
  exit 1
fi

# Detecta o comando do Compose (V2 preferido, fallback para o legado).
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

# --- .env ---
echo -e "${YELLOW}[1/5]${NC} Verificando configuração (.env)..."
if [ ! -f "$ROOT_DIR/.env" ]; then
  if [ -f "$ROOT_DIR/.env_example" ]; then
    cp "$ROOT_DIR/.env_example" "$ROOT_DIR/.env"
    echo -e "  ${GREEN}✓${NC} .env criado a partir de .env_example"
    echo -e "  ${YELLOW}⚠ Revise o .env e defina senhas fortes antes de usar em produção real.${NC}"
  else
    echo -e "  ${RED}✗ Não encontrei .env nem .env_example. Não é possível iniciar.${NC}"
    exit 1
  fi
else
  echo -e "  ${GREEN}✓${NC} .env encontrado"
fi

# Lê um valor do .env (primeira ocorrência); imprime vazio se não existir.
env_get() { grep -E "^$1=" "$ROOT_DIR/.env" 2>/dev/null | head -n1 | cut -d= -f2- || true; }

# Grava/atualiza uma chave no .env de forma idempotente.
env_set() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ROOT_DIR/.env"; then
    # Usa | como separador para não colidir com / nos valores.
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
    echo -e "  ${GREEN}✓${NC} SECRET_KEY forte gerada no .env"
  else
    echo -e "  ${YELLOW}⚠ Defina um SECRET_KEY forte no .env (python3 não encontrado para gerar).${NC}"
  fi
fi

# --- Escolha do ambiente ---
echo ""
echo -e "${YELLOW}[2/5]${NC} Escolhendo o ambiente..."
APP_ENV=""
if [ -n "$ENV_ARG" ]; then
  APP_ENV="$ENV_ARG"
elif [ -t 0 ]; then
  echo -e "  Em qual ambiente você quer rodar?"
  echo -e "    ${CYAN}1)${NC} Sandbox  — ambiente de TESTES, banco próprio (pode experimentar à vontade)"
  echo -e "    ${CYAN}2)${NC} Produção — ambiente REAL, banco principal"
  default_choice=2; [ "$CURRENT_ENV" = "sandbox" ] && default_choice=1
  read -r -p "  Digite 1 ou 2 [padrão: ${default_choice}]: " choice || true
  choice="${choice:-$default_choice}"
  case "$choice" in
    1) APP_ENV="sandbox" ;;
    2) APP_ENV="production" ;;
    *) echo -e "  ${YELLOW}Opção inválida; usando o padrão.${NC}"
       [ "$default_choice" = "1" ] && APP_ENV="sandbox" || APP_ENV="production" ;;
  esac
else
  # Sem terminal e sem argumento: mantém o que está no .env.
  APP_ENV="$CURRENT_ENV"
fi

env_set APP_ENV "$APP_ENV"
if [ "$APP_ENV" = "sandbox" ]; then
  echo -e "  ${GREEN}✓${NC} Ambiente: ${CYAN}SANDBOX${NC} (testes)"
else
  echo -e "  ${GREEN}✓${NC} Ambiente: ${CYAN}PRODUÇÃO${NC}"
fi

# Portas e credenciais do banco (para health check e criação do banco sandbox).
API_PORT="$(env_get API_PORT)"; API_PORT="${API_PORT:-8000}"
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
    sleep 1; printf "  Tentativa %d/%d...\r" "$retry" "$MAX_RETRIES"
  done
  return 0
}

# --- Banco: sobe o Postgres primeiro e garante o banco do ambiente ---
echo ""
echo -e "${YELLOW}[3/5]${NC} Preparando o banco de dados..."
$DC up $BUILD_FLAG -d db > "$COMPOSE_UP_LOG" 2>&1 || { tail -8 "$COMPOSE_UP_LOG"; echo -e "  ${RED}✗ Falha ao subir o banco.${NC}"; exit 1; }

# Espera o Postgres aceitar conexões.
db_retry=0
until $DC exec -T db pg_isready -U "$DB_USER" >/dev/null 2>&1; do
  db_retry=$((db_retry + 1)); [ "$db_retry" -ge "$MAX_RETRIES" ] && { echo -e "  ${RED}✗ Banco não ficou pronto.${NC}"; break; }
  sleep 1; printf "  Aguardando o banco %d/%d...\r" "$db_retry" "$MAX_RETRIES"
done
echo -e "  ${GREEN}✓${NC} Banco de dados pronto            "

# Em sandbox, garante que o banco isolado exista (com PostGIS).
if [ "$APP_ENV" = "sandbox" ]; then
  if ! $DC exec -T db psql -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='${SANDBOX_DB_NAME}'" 2>/dev/null | grep -q 1; then
    $DC exec -T db psql -U "$DB_USER" -c "CREATE DATABASE ${SANDBOX_DB_NAME};" >/dev/null 2>&1 || true
    $DC exec -T db psql -U "$DB_USER" -d "${SANDBOX_DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS postgis;" >/dev/null 2>&1 || true
    echo -e "  ${GREEN}✓${NC} Banco de sandbox criado (${SANDBOX_DB_NAME})"
  else
    echo -e "  ${GREEN}✓${NC} Banco de sandbox já existe (${SANDBOX_DB_NAME})"
  fi
fi

# --- Sobe o restante e recria o backend para reler o APP_ENV ---
echo ""
echo -e "${YELLOW}[4/5]${NC} Subindo os serviços (${APP_ENV})..."
$DC up $BUILD_FLAG -d --remove-orphans >> "$COMPOSE_UP_LOG" 2>&1 || true
# O backend lê o APP_ENV no boot: recria só ele para pegar o ambiente escolhido.
$DC up -d --force-recreate --no-deps backend >> "$COMPOSE_UP_LOG" 2>&1 || true
tail -3 "$COMPOSE_UP_LOG"

HEALTH_RC=0; wait_for_backend || HEALTH_RC=$?
if [ "$HEALTH_RC" -eq 2 ]; then
  echo -e "  ${YELLOW}⚠ Rede do Docker instável (serviço 'db' não resolvido). Recriando uma vez...${NC}"
  $DC down --remove-orphans || true   # nunca -v: preserva os dados
  $DC up $BUILD_FLAG -d --remove-orphans >> "$COMPOSE_UP_LOG" 2>&1 || true
  HEALTH_RC=0; wait_for_backend || HEALTH_RC=$?
fi

if [ "$HEALTH_RC" -eq 0 ]; then
  echo -e "  ${GREEN}✓${NC} Backend saudável (porta ${API_PORT})     "
else
  echo -e "  ${RED}✗ O backend não ficou saudável.${NC}"
  if grep -q "address already in use" "$COMPOSE_UP_LOG" 2>/dev/null; then
    echo -e "  ${YELLOW}Uma porta já está em uso. Libere-a ou mude a *_PORT no .env.${NC}"
  fi
  echo -e "  ${YELLOW}Dica: veja os logs com '${DC} logs backend'${NC}"
fi

# Alembic stamp guard (instalações antigas com tabelas pré-Alembic).
$DC exec -T backend bash -c "
  alembic current 2>&1 | grep -qE '(head|\(head\))' ||
  (alembic current 2>&1 | grep -qi 'no current revision' && alembic stamp head 2>&1) || true
" >/dev/null 2>&1 || true

# --- Usuário de acesso do ambiente: cria ou atualiza a senha do .env ---
echo ""
echo -e "${YELLOW}[5/5]${NC} Preparando o usuário de acesso..."
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
  created) echo -e "  ${GREEN}✓${NC} Usuário criado e pronto para uso" ;;
  updated) echo -e "  ${GREEN}✓${NC} Usuário atualizado (senha do .env aplicada)" ;;
  *)       echo -e "  ${YELLOW}⚠ Não consegui preparar o usuário (${BOOTSTRAP_RESULT}). Veja '${DC} logs backend'.${NC}" ;;
esac

# --- Frontend ---
echo ""
echo -e "${YELLOW}[extra]${NC} Preparando o frontend..."
cd "$FRONTEND_DIR"
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
  if [ "$NODE_MAJOR" -lt 20 ] 2>/dev/null; then
    echo -e "  ${YELLOW}⚠ Seu Node é v$(node -v 2>/dev/null). O frontend precisa do Node 20+.${NC}"
    echo -e "  ${YELLOW}  Instale uma versão 20+ (ex.: via nvm ou fnm) para o painel abrir.${NC}"
  fi
else
  echo -e "  ${YELLOW}⚠ Node não encontrado. Instale o Node 20+ para rodar o frontend.${NC}"
fi
if [ ! -d "node_modules" ]; then
  echo -e "  Instalando dependências do frontend..."
  npm install --silent || echo -e "  ${YELLOW}⚠ Falha ao instalar dependências do frontend.${NC}"
fi

# --- Painel final ---
ENV_LABEL="PRODUÇÃO"; [ "$APP_ENV" = "sandbox" ] && ENV_LABEL="SANDBOX (testes)"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                GeoAvia está no ar!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo -e "  Ambiente:  ${CYAN}${ENV_LABEL}${NC}"
echo -e "  Sistema:   ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "  API/Docs:  ${CYAN}http://localhost:${API_PORT}/docs${NC}"
echo -e "  Airflow:   ${CYAN}http://localhost:${AIRFLOW_PORT}${NC}"
echo ""
echo -e "  ${GREEN}Entre no sistema com:${NC}"
echo -e "    Usuário: ${CYAN}${BOOT_USER}${NC}"
echo -e "    Senha:   ${CYAN}${BOOT_PASS}${NC}"
echo ""
echo -e "  ${YELLOW}Novos usuários criados pelo admin recebem um código de primeiro${NC}"
echo -e "  ${YELLOW}acesso e definem a própria senha no link da tela de login.${NC}"
echo ""
echo -e "  ${YELLOW}O frontend vai iniciar abaixo. Pressione Ctrl+C para parar.${NC}"
echo ""

npm run dev
