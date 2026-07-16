# Architecture Decision Records (ADRs)

This folder records significant architectural decisions for GeoAvia, so future
contributors (and audits) can understand *why* the system is built the way it
is — not just *what* the code does.

Each ADR is a short, immutable document with a status (Proposed / Accepted /
Superseded). New decisions get a new file; when a decision changes, add a new
ADR that supersedes the old one instead of rewriting history.

## Records

- [0001 — Record architecture decisions](0001-record-architecture-decisions.md)
- [0002 — Raw SQL, no ORM](0002-raw-sql-no-orm.md)
- [0003 — Layered backend architecture](0003-layered-architecture.md)
- [0004 — Three-role RBAC and the developer sandbox](0004-rbac-three-roles-and-sandbox.md)
- [0005 — Password reset via admin-issued code](0005-password-reset-by-admin-code.md)
- [0006 — Raster analytic core: on-disk COGs + rasterio/NumPy MCDA](0006-raster-analytic-core.md)
- [0007 — Reproducible deploy via a versioned demo seed (no Git LFS)](0007-reproducible-deploy-demo-seed.md)
