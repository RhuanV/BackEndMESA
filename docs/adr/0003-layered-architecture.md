# 0003 — Layered backend architecture

**Status:** Accepted

## Context

Endpoint logic, business rules and database access were previously mixed in a
single large `main.py`. This made the code hard to test and reason about.

## Decision

The backend package `geoavia_backend` is organized in layers:

- `api/` — one FastAPI router per domain; `main.py` only assembles the app.
- `services/` — business rules and orchestration.
- `repositories/` — data access via parameterized SQL.
- `core/` — cross-cutting concerns (auth, db, roles, sandbox, config).
- `schemas/` — Pydantic request/response models.

Dependencies flow one way: api → services → repositories. Cross-cutting rules
(role gates, sandbox) live in `core` and are shared by the routers.

## Consequences

- Each layer is independently testable (see `backend/tests/`).
- New domains follow the same api/service/repository shape.
- A little more boilerplate per feature, accepted for clarity and testability.
