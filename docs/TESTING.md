# Manual de Testes — GeoAvia

Guia completo para testar o projeto rodando, cobrindo **testes automatizados** (backend,
frontend, Airflow) e **testes manuais end-to-end**, nos dois modos de ambiente:
**sandbox** (`APP_ENV=sandbox`) e **produção/fora do sandbox** (`APP_ENV=production`).

> **Ponto-chave:** o modo de ambiente afeta **apenas o role `desenvolvedor`**. Em `sandbox` ele
> tem escrita total; em `production` ele é **read-only** — toda tentativa de escrita retorna
> **403** e é registrada no log de auditoria. Operador e administrador escrevem normalmente nos
> dois modos.

---

## 1. Pré-requisitos

- **Docker + Docker Compose V2**, **Node.js/npm**, e (opcional) **Python 3.12** para rodar o
  backend localmente.
- Crie o `.env` a partir do template:

  ```bash
  cp .env_example .env
  ```

- Variáveis relevantes para teste (ver [.env_example](../.env_example)):

  | Variável | Papel no teste | Default |
  |----------|----------------|---------|
  | `APP_ENV` | `sandbox` (dev escreve) ou `production` (dev read-only) | `sandbox` no template |
  | `DEV_USER` / `DEV_PASS` / `DEV_ROLE` | usuário bootstrap criado no startup | `admin` / `admin123` / `desenvolvedor` |
  | `SHAPEFILE_MAX_UPLOAD_MB` | limite de upload de shapefile | `500` |
  | `SECRET_KEY` / `ALGORITHM` | assinatura JWT | — / `HS256` |

---

## 2. Subir o projeto

```bash
bash install.sh   # primeira vez: build das imagens Docker + deps do frontend
bash start.sh      # pergunta o ambiente (sandbox/produção), sobe tudo e prepara o usuário
```

O `start.sh` pergunta em qual ambiente rodar (ou aceita `./start.sh sandbox` / `./start.sh prod`),
cria o banco de sandbox se necessário, recria o backend no ambiente escolhido e garante o usuário de
acesso (admin em produção, dev em sandbox) com a senha do `.env`, mostrando as credenciais no fim.

Serviços e URLs:

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | `admin` / `admin123` |
| API / Swagger | http://localhost:8000/docs | Bearer token (JWT) |
| Airflow UI | http://localhost:8080 | `admin` / `admin` |
| PostgreSQL | localhost:5433 | `postgres` / `123` |

---

## 3. Testes automatizados

| Parte | Comando | Observação |
|-------|---------|------------|
| **Backend** | `pytest backend/tests -q` | unitário, **não precisa de DB** (fakes em memória) |
| **Backend (container)** | `docker compose exec backend pytest` | como roda em ambiente Docker |
| **Frontend** | `cd frontend && npm run lint && npm run test && npm run build` | ESLint + Vitest + type-check/build |
| **Airflow** | `bash run_airflow_tests.sh` | requer o stack de pé (container `geoavia_airflow`) |

Estes são os mesmos passos executados pelo CI em [.github/workflows/ci.yml](../.github/workflows/ci.yml).

**Backend** — testes em [backend/tests/](../backend/tests/): `test_app_smoke.py`, `test_roles.py`,
`test_password_recovery.py`, `test_sandbox.py`.

**Frontend** — testes em [frontend/src/](../frontend/src/): `types/auth.test.ts`,
`features/auth/schemas/resetPasswordSchema.test.ts`.

**Airflow** — 6 módulos em [tests/airflow/](../tests/airflow/) (integridade de DAGs, conexão com
DB, scheduler, inicialização, execução de tasks, tratamento de falhas).

> O aviso `Some chunks are larger than 500 kB` no `npm run build` é apenas um **warning** de
> tamanho de bundle — o build passa. Não é erro e não afeta os testes.

---

## 4. Testar o toggle sandbox vs produção

Comportamento imposto pelo middleware `sandbox_guard` em
[backend/src/geoavia_backend/main.py](../backend/src/geoavia_backend/main.py), com a lógica em
[backend/src/geoavia_backend/core/sandbox.py](../backend/src/geoavia_backend/core/sandbox.py).
`APP_ENV` é lido a cada requisição pelo middleware, então basta reiniciar o backend após mudar o `.env`.

> **Isolamento de dados por banco.** Além do bloqueio de escrita, sandbox e produção usam **bancos
> diferentes**: `APP_ENV=sandbox` conecta em `SANDBOX_DB_NAME` (`geoavia_sandbox_db`), produção em
> `DB_NAME` (`geoavia_main_db`) — ver [core/database.py](../backend/src/geoavia_backend/core/database.py).
> A escolha do banco é por processo (lida no boot), então **reinicie o backend** ao trocar de ambiente.
> Dados criados em sandbox (usuários, assessments, etc.) **não aparecem** em produção. O sandbox começa
> sem os dados geográficos carregados pelo Airflow (que vivem no banco principal).

### 4.3 Verificar o isolamento de dados

1. Em `APP_ENV=sandbox`, crie um usuário (`POST /users/signup`) — ex.: `bob`.
2. Troque para `APP_ENV=production`, reinicie o backend e faça `GET /users`: **`bob` não aparece**.
3. Volte para `sandbox`, reinicie: `bob` reaparece.
4. Os dois bancos coexistem: `docker compose exec db psql -U postgres -l` lista `geoavia_main_db`
   e `geoavia_sandbox_db`.

### 4.1 Modo sandbox (`APP_ENV=sandbox`)

1. No `.env`: `APP_ENV=sandbox`. Reinicie o backend:
   ```bash
   docker compose up -d backend    # ou: bash start.sh
   ```
2. Login como `admin` (role `desenvolvedor`). No Swagger (http://localhost:8000/docs), autorize
   com o token e execute uma **escrita** — ex.: `POST /assessments`, `POST /shapefiles/upload`
   ou `PUT /layers/{layer_name}/source`.
3. **Esperado:** sucesso (2xx). Na UI, as rotas `/dashboard/dev/*` ficam acessíveis.

### 4.2 Modo produção (`APP_ENV=production`)

1. No `.env`: `APP_ENV=production`. Reinicie o backend.
2. Login como `desenvolvedor`; repita a mesma escrita.
3. **Esperado:** **403** com o detalhe:
   > "Developer role is read-only in production (sandbox mode). Use an administrador account, or
   > set APP_ENV=sandbox in a non-production environment."
4. Confirme que **GET** (leitura) continua funcionando para o desenvolvedor.
5. Confirme que **administrador e operador escrevem normalmente** em ambos os modos (o toggle não
   os afeta). Crie um administrador via `POST /users/signup` para testar.

Inspecionar a auditoria (toda tentativa de escrita do desenvolvedor é logada, em ambos os modos):

```bash
docker compose logs backend | grep "developer write"
```

---

## 5. Matriz de acesso por role (RBAC)

Roles definidos em [backend/src/geoavia_backend/core/roles.py](../backend/src/geoavia_backend/core/roles.py);
gating de rotas no frontend em [frontend/src/app/](../frontend/src/app/).

| Ação | operador | administrador | desenvolvedor |
|------|:--:|:--:|:--:|
| Login, Map, Assessment, Analysis, Results, Export, Screening, Upload shapefile, Trigger DAG | ✓ | ✓ | ✓ |
| Gerir usuários / Config de layers / Audit (`/dashboard/admin/*`) | ✗ | ✓ | ✓ |
| Dev tools (`/dashboard/dev/health`, `/logs`, `/debug`) | ✗ | ✗ | ✓ |
| Escrita (POST/PUT/PATCH/DELETE) | ✓ | ✓ | só em `APP_ENV=sandbox` |

> Apenas um `desenvolvedor` pode conceder o role `desenvolvedor` a outro usuário. O `DEV_USER`
> bootstrap é protegido (não pode ser deletado, ter username/senha alterados por rotas normais,
> nem receber código de recuperação).

**Teste das guardas de rota:** logado como operador, tente abrir `/dashboard/admin/users` e
`/dashboard/dev/health` → deve ser bloqueado/redirecionado.

---

## 6. Fluxos funcionais end-to-end (UI + API)

Cada fluxo com passos concretos e testes negativos. Faça-os uma vez em `sandbox` e uma em
`production` (com o role desenvolvedor) para validar o comportamento de escrita.

### 6.1 Login + rate-limiting
- **UI:** http://localhost:5173/login · **API:** `POST /login` (form: `username`, `password`).
- Sucesso → redirect para `/dashboard/map`, token JWT com role.
- Negativos: credenciais inválidas → erro genérico; **5 falhas** → cooldown progressivo (3s, 6s…).

### 6.2 Recuperação de senha (admin gera código)
- **API:** `POST /users/{user_id}/recovery-code` (admin) → `POST /password-reset` (público).
- Código de **8 caracteres**, TTL **30 min**, **single-use**, máx. **5 tentativas** falhas, hasheado
  em repouso. `DEV_USER` não pode receber código.
- Fluxo: admin gera código → usuário faz reset com `{username, code, new_password}` → login com a
  nova senha. Negativos: código inválido/expirado/queimado, senha < 8 chars.

### 6.3 Upload de shapefile (HU-31)
- **UI:** `/dashboard/data/shapefiles` · **API:** `POST /shapefiles/upload` (multipart),
  `GET /shapefiles`, `GET /shapefiles/{id}/features`.
- ZIP com `.shp` + `.dbf` + `.shx` (+ `.prj`); limite `SHAPEFILE_MAX_UPLOAD_MB` (500 MB);
  reprojeta para **EPSG:4674** (SIRGAS 2000).
- Negativos: arquivo não-`.zip`, `> 500 MB`, ZIP inválido/não-shapefile.

### 6.4 Fluxo MESA (Assessment → Analysis → Results → Export)
- `POST /assessments` (UI `/dashboard/assessment`) — valida ranges (slope 0–100, lat −90..90, etc.).
- `POST /analysis/run` (UI `/dashboard/analysis`) — **pesos devem somar 100%**, senão **400**;
  retorna `job_id`. Acompanhe com `GET /analysis/status/{job_id}`.
- `GET /ranking` (UI `/dashboard/results`) — ranking por score.
- `GET /export/shapefile` e `GET /export/csv` (UI `/dashboard/export`).
  `GET /export/geotiff` → **501** (não implementado); export sem assessments → **400**.

### 6.5 Trigger de DAG do Airflow via API
- **API:** `POST /airflow/trigger/{dag_id}` (whitelist de DAGs), `GET /airflow/triggers`.
- DAG fora da whitelist → **404**. Cada trigger é auditado (quem disparou, dag_run_id, status).
- Nota: DAGs OSM exigem rodar antes o `download_geofabrik_data` na UI do Airflow (~1–1.5 GB).

---

## 7. Rodar tudo — checklist rápido

```bash
# 1. Automatizados
pytest backend/tests -q
cd frontend && npm run lint && npm run test && npm run build && cd ..
bash run_airflow_tests.sh          # após bash start.sh

# 2. Manual E2E (seção 6), executado duas vezes:
#    - uma com APP_ENV=sandbox
#    - uma com APP_ENV=production  (para validar o dev read-only + 403 + auditoria)
```

---

## 8. Limites atuais

- **Sem medição de cobertura** (`pytest-cov` não configurado) e **sem E2E automatizado**
  (Playwright/Cypress) — a seção 6 é manual.
- O **pre-commit** ([.pre-commit-config.yaml](../.pre-commit-config.yaml)) valida apenas a
  mensagem de commit (Conventional Commits); não roda testes.
