# 0001 — Record architecture decisions

**Status:** Accepted

## Context

GeoAvia is developed by a rotating team and is subject to audit. Decisions about
security, data access and architecture were previously implicit in the code and
in pull-request discussions, making them hard to recover later.

## Decision

We keep lightweight Architecture Decision Records (ADRs) under `docs/adr/`. Each
records one decision, is immutable once accepted, and is superseded by a new ADR
rather than edited. Records use the format: Title / Status / Context / Decision /
Consequences.

## Consequences

- New significant decisions must be captured as an ADR in the same PR.
- Reviewers and auditors get a durable rationale for how the system is built.
- A small, ongoing documentation cost is accepted in exchange for traceability.
