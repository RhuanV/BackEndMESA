"""Persistence for the security/action audit log.

The audit log is append-only: rows are only ever inserted and read, never
updated or deleted. All queries are parameterized (never string-formatted) to
keep the log injection-safe.
"""

from __future__ import annotations

from geoavia_backend.core.db import cursor


class AuditRepository:
    def insert(
        self,
        user_id: int | None,
        username: str | None,
        user_role: str | None,
        action: str,
        resource: str | None = None,
        detail: str | None = None,
        ip_address: str | None = None,
    ) -> int:
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_log
                    (user_id, username, user_role, action, resource, detail, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, username, user_role, action, resource, detail, ip_address),
            )
            return cur.fetchone()[0]

    def list_recent(
        self,
        limit: int = 100,
        offset: int = 0,
        action: str | None = None,
        username: str | None = None,
    ) -> list[dict]:
        """Returns audit entries newest first, with optional filters.

        `action` and `username` are matched exactly and passed as bound
        parameters, so the filters are injection-safe.
        """
        clauses: list[str] = []
        params: list[object] = []
        if action:
            clauses.append("action = %s")
            params.append(action)
        if username:
            clauses.append("username = %s")
            params.append(username)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])

        with cursor(dict_rows=True) as cur:
            cur.execute(
                f"""
                SELECT id, user_id, username, user_role, action, resource,
                       detail, ip_address, created_at
                FROM audit_log
                {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
                """,
                tuple(params),
            )
            return cur.fetchall()
