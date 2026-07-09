# 0004 — Three-role RBAC and the developer sandbox

**Status:** Accepted

Supersedes the previous six-role model (coordenador, gestor, supervisor,
operador, administrador, desenvolvedor).

## Context

The six roles overlapped heavily and diverged between frontend and backend,
which is a security risk and hard to reason about. The team needs a simple,
auditable model matching how the system is actually operated.

## Decision

Three roles, defined once in `core/roles.py` (backend) and mirrored in the
frontend:

- **operador** — operates the program (maps, analyses, assessments, results,
  export, screening, shapefile upload). No admin or developer powers.
- **administrador** — everything an operador does, plus user management
  (create/update/delete users and issue password-recovery codes), layer/source
  configuration and audit. No developer tools.
- **desenvolvedor** — everything, including developer tools, but *sandboxed*:
  governed by `APP_ENV`. In `production` the role is read-only — every mutating
  request (POST/PUT/PATCH/DELETE) is audited and blocked (HTTP 403) by a
  middleware; in `sandbox` it has full write access. The default is production
  (fail-safe). Granting the `desenvolvedor` role is restricted to developers.

## Consequences

- One source of truth for gates; frontend and backend stay aligned.
- Developers can inspect everything in production without risking real data.
- Requires setting `APP_ENV=sandbox` in non-production environments for
  developers to have write access there.
