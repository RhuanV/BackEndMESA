# 0002 — Raw SQL, no ORM

**Status:** Accepted

## Context

The domain is heavily geospatial (PostGIS): reprojections, `ST_*` functions,
on-the-fly geometry simplification and bbox filtering. ORMs add an abstraction
layer that fits these queries poorly and hides the SQL that reviewers must
audit.

## Decision

The repository layer uses parameterized raw SQL via `psycopg2`, centralized
through the `cursor()` helper in `core/db.py`. SQLAlchemy is present only as the
engine Alembic uses to run migrations; there is no ORM model layer. All
user-supplied values are passed as query parameters (never string-interpolated)
to prevent SQL injection.

## Consequences

- Full control over PostGIS SQL and query performance.
- Developers must write SQL by hand and keep it parameterized.
- The schema's source of truth is Alembic migrations, not ORM models
  (see [0003](0003-layered-architecture.md)).
