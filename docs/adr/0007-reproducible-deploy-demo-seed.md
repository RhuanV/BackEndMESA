# 0007 — Reproducible deploy via a versioned demo seed (no Git LFS)

**Status:** Accepted

## Context

A fresh deploy must work **using only what is in the GitHub repository**, with
no dependency on live government downloads (which are large, slow and sometimes
unreachable). The app needs some real geodata to be visibly functional out of
the box: state boundaries (already seeded by migration `0018` from
`backend/seed/state_boundaries.sql.gz`), plus — for Phases 4/5 — a município
with its vector layers and the slope/land-use rasters.

## Decision

Ship a small **demo município** as versioned seed data, loaded idempotently
during `alembic upgrade head` (same pattern as migration `0018`):

- Vector layers → gzipped SQL (`backend/seed/demo_<ibge>_vetor.sql.gz`).
- Rasters → clipped GeoTIFFs (`backend/seed/demo_<ibge>_*.tif`).

The demo município is chosen to be **small in area** so every seed file stays a
few MB — small enough for **plain Git**. We deliberately **do not use Git LFS**:
a plain `git clone` then `docker compose up` must just work, with no
`git lfs pull` step. `.gitattributes` marks the seed files as binary so they are
not line-ending–normalized. If a future need arises to commit national datasets,
Git LFS is the documented path (`docs/DEPLOY.md`), but the shipped seed avoids
that dependency.

The Airflow download DAGs remain the mechanism for real/ongoing ingestion and
for regenerating the seed (`backend/scripts/make_demo_seed`); provenance and
licensing of the seed data are recorded in `backend/seed/PROVENANCE.md`.

## Consequences

- `git clone` + `docker compose up` yields a working app offline from gov sources.
- Seed size is bounded by keeping the demo município small; large national data
  stays out of the repo.
- The seed is regenerable and its provenance auditable; the same loader path is
  reused, so there is no bespoke deploy tooling.
