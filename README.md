# GeoAvia - Backend MESA-Auto

Backend do framework GeoAvia (parceria SAC/ANAC/ITA) para automatizar a **Metodologia MESA** na prospeccao de sitios aeroportuarios.

O projeto foi desenvolvido com:

- Python 3.12
- FastAPI
- PostgreSQL (com evolucao prevista para PostGIS)
- Docker e Docker Compose

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Configuracao](#configuracao)
- [Documentacao da API](#documentacao-da-api)
- [Diretrizes para IA](#diretrizes-para-ia)

## Visao Geral

Este backend implementa uma arquitetura em camadas para separar claramente:

- Interface HTTP (API)
- Regras de negocio da metodologia MESA
- Acesso a dados no PostgreSQL via SQL puro

## Arquitetura

```text
Camada 3 -> API (FastAPI)
Camada 2 -> Service (regras de negocio MESA)
Camada 1 -> Repository (SQL puro com psycopg2)
```

Principios adotados:

- Sem ORM neste momento, priorizando controle e performance para operacoes geograficas
- Regras de negocio concentradas na camada Service
- Configuracao por variaveis de ambiente (`.env`)

## Estrutura do Projeto

```text
BackEndMESA/
|-- backend/
|   |-- main.py          # Camada 3: API/rotas
|   |-- service.py       # Camada 2: regras de negocio MESA
|   |-- repository.py    # Camada 1: acesso ao banco (SQL puro)
|   `-- database.py      # configuracao e leitura do .env
|-- init-db/
|   |-- 01_create_tables.sql
|   `-- 02_insert_data.sql
|-- .github/
|   `-- copilot-instructions.md
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## Como Executar

### Opcao A: Docker (recomendado)

Sobe automaticamente PostgreSQL + API FastAPI.

1. Configure o arquivo `.env` na raiz (veja a secao [Configuracao](#configuracao)).
2. Execute:

```bash
docker-compose up --build
```

O banco sera inicializado com os scripts da pasta `init-db/`.

### Opcao B: Execucao local

1. Crie e ative o ambiente virtual:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Execute a API:

```bash
python -m uvicorn backend.main:app --reload
```

## Configuracao

Crie um arquivo `.env` na raiz com o conteudo:

```env
DB_HOST=db
DB_NAME=geoavia
DB_USER=postgres
DB_PASS=sua_senha_secreta
DB_PORT=5432
```

Observacao:

- Use `DB_HOST=localhost` se executar a API fora do Docker

## Documentacao da API

Com o servidor em execucao:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Diretrizes para IA

As diretrizes de arquitetura e contexto tecnico para assistentes de IA estao em:

- `.github/copilot-instructions.md`
- `docs/adr/` (Architecture Decision Records)

Decisoes principais:

- SQL puro com `psycopg2-binary` para facilitar evolucao geoespacial
- Logica MESA centralizada na camada `service.py`