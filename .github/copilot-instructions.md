# Project Context: GeoAvia (MESA-Auto)

## Overview
This project is a partnership between SAC/ANAC/ITA to automate the prospecting of airport sites using the MESA methodology.

## Technical Stack
- **Backend:** FastAPI (Python 3.12)
- **Database:** PostgreSQL (future PostGIS) via Docker
- **Architecture:** Layered (Main/API -> Service -> Repository)

## Implementation Rules
1. **Repository:** Only use raw SQL with `psycopg2-binary`. Do not use an ORM for now in order to maintain geographic performance.
2. **Service:** Exclusive place for MESA business rules (Eliminatory and Classificatory Criteria).
3. **Environment:** Everything must be compatible with Docker Compose. Credentials must always come from `.env`.

## Code Standards
- Use Python type hints in all functions.
- Always write code, comments and docstrings in English.
- When creating a new file, add a comment at the top explaining the purpose of the file and how it fits into the overall architecture.

## 🔒 Security and Authentication (Login & RBAC)

When implementing user features, login, or route protection, follow these mandatory guidelines:

### 1. Credential Handling
- **Plain Text Prohibition:** Never store or compare passwords in plain text.
- **Hashing:** Mandatory use of the `passlib` library with the **bcrypt** algorithm.
- **Salting:** Ensure the salt is generated automatically by the hashing library.
- **Repository Layer:** The repository must only retrieve the hash from the database by `username`. Logical comparison must occur in the **Service** layer.

### 2. Authentication Flow (JWT)
- **Tokens:** Use **JSON Web Tokens (JWT)** for session persistence.
- **Payload:** The token must contain `sub` (user ID), `username`, `exp` (expiration), and **must include** the `role` field (user profile).
- **Token Security:** The `SECRET_KEY` used to sign the JWT must be strictly read from the `.env` file through `database.py`.

### 3. Authorization and Roles (RBAC)
The system must support three access levels (Role-Based Access Control):

- **Analyst:** Access to site queries, MESA data entry, and map visualization.
- **Administrator:** User management, modification of criteria weights, and report approval.
- **Developer:** Access to system logs, performance metrics, and maintenance endpoints.

### 4. FastAPI Implementation
- Use FastAPI’s `OAuth2PasswordBearer` to extract tokens.
- Create **Dependencies** (injectable functions) to verify whether the role contained in the token has permission to access the specific route.
- Return `401 Unauthorized` for login failures and `403 Forbidden` for authenticated users attempting to access routes above their permission level.

### 5. Code Layers
- **backend/repository.py:** Methods for `get_user_by_username` and `create_user`.
- **backend/service.py:** Logic for `verify_password`, `get_password_hash`, `authenticate_user`, and `create_access_token`.
- **backend/main.py:** Endpoints `/login`, `/signup`, and application of security dependencies on protected routes.s