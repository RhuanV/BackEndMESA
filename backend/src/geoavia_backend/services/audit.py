"""Audit service: records security-relevant events to the audit log.

`record()` is intentionally best-effort — auditing must never break the request
it is observing. If the insert fails (e.g. the DB is briefly unavailable) the
error is logged to the `geoavia.audit` logger and swallowed, so the caller's
main flow proceeds. Callers must never pass secrets (passwords, tokens, the DSN)
in `detail`.
"""

from __future__ import annotations

import logging

from geoavia_backend.repositories.audit import AuditRepository

audit_logger = logging.getLogger("geoavia.audit")

# Canonical action names recorded in the audit log.
LOGIN = "LOGIN"
LOGIN_FAILED = "LOGIN_FAILED"
LOGOUT = "LOGOUT"
USER_CREATE = "USER_CREATE"
USER_DELETE = "USER_DELETE"
EXPORT = "EXPORT"
ANALYSIS_RUN = "ANALYSIS_RUN"
DEV_WRITE_BLOCKED = "DEV_WRITE_BLOCKED"

# Detail text is bounded so a caller can never bloat the log with a huge string.
_MAX_DETAIL = 1000


class AuditService:
    def __init__(self) -> None:
        self.repo = AuditRepository()

    def record(
        self,
        action: str,
        user_id: int | None = None,
        username: str | None = None,
        user_role: str | None = None,
        resource: str | None = None,
        detail: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Persists an audit entry. Never raises: failures are logged, not thrown."""
        try:
            self.repo.insert(
                user_id=user_id,
                username=username,
                user_role=user_role,
                action=action,
                resource=resource,
                detail=detail[:_MAX_DETAIL] if detail else None,
                ip_address=ip_address,
            )
        except Exception:  # noqa: BLE001 — auditing must not break the caller
            audit_logger.exception("failed to record audit event %s", action)
