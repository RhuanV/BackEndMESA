# GeoAvia - Backend MESA-Auto

Backend for the GeoAvia project (SAC/ANAC/ITA partnership) for automating the MESA methodology in airport site prospecting.

## Overview

Current stack:

- Python 3.12
- FastAPI
- PostgreSQL (with planned evolution to PostGIS)
- Docker and Docker Compose
- Raw SQL with psycopg2 (no ORM)

Current API state:

- User registration with password hashing
- Login with JWT
- Route protection using Bearer token on GET /usuarios
- User management by ID (update username and delete)

## Architecture

Layered architecture:

- API Layer: backend/main.py
- Service Layer: backend/service.py
- Repository Layer: backend/repository.py
- Environment configuration: backend/database.py

Principles:

- Business rules in the service layer
- Data access in the repository using explicit SQL
- Sensitive variables managed through .env

## Repository Structure

```text
BackEndMESA/
|-- backend/
|   |-- main.py
|   |-- service.py
|   |-- repository.py
|   `-- database.py
|-- init-db/
|   |-- 01_create_tables.sql
|   `-- 02_insert_data.sql
|-- .github/
|   `-- copilot-instructions.md
|-- .pre-commit-config.yaml
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## Configurations

Create a .env file in the root directory with:

```env
DB_HOST=db
DB_NAME=geoavia_users
DB_USER=postgres
DB_PASS=123
DB_PORT=5432
SECRET_KEY=change_for_a_strong_password
ALGORITHM=HS256
```

Notes:

- When running locally outside Docker, use DB_HOST=localhost.
- SECRET_KEY must be unique per environment and should not be versioned.

## How to Run

### Option A: Docker (recommended)

```bash
docker-compose up --build
```

Expected services:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Database: port 5433 on the host (mapped to 5432 inside the container)

If you already have PostgreSQL running locally, you may need to connect using port 5433 in DBeaver (or another DB client) to view the database during tests.

### Opção B: Local

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

Install dependencies and start:

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

## Current Endpoints

Authentication:

- POST /usuarios/signup
- POST /login

Users:

- GET /usuarios (protected with token)
- PUT /usuarios/{user_id}/username
- DELETE /usuarios/{user_id}

## Authentication Flow

- Create a user with POST /usuarios/signup
- Authenticate with POST /login
- Receive access_token
- Send Authorization: Bearer <token> when calling GET /usuarios

## Colaboration Guidelines

Practical suggestions to evolve the repository as a team:

1. Separate the security module
    - Create backend/security.py to centralize hashing, token generation, and validation.
    - Keep backend/service.py focused on business logic.
2. Standardize request/response models
    - Create backend/schemas.py with Pydantic classes for signup, login, and responses.
    - Reduce loose parameters in route definitions.
3. Separate runtime and development dependencies
    - Keep runtime dependencies in requirements.txt.
    - Create requirements-dev.txt for tools like pre-commit and commitizen.
4. Add automated tests
    - tests/unit for service layer tests.
    - tests/integration for routes and authentication.
5. Define collaboration conventions
    - Branch pattern: feat/, fix/, chore/.
    - Pull requests with a minimum checklist (local testing, API impact, database migration).
    - Semantic commits using commitizen (already supported by .pre-commit-config.yaml).
6. Version architectural decisions
    - Create a docs/adr folder to document decisions about security, database, and API design.

## Security

- Passwords must never be stored in plain text.
- Do not commit .env files containing real credentials.
- In production, rotate SECRET_KEY and use secure environment variables.

## Internal References

- Implementation guidelines: .github/copilot-instructions.md
- API entry point: backend/main.py