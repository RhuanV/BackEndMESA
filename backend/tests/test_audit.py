"""Audit service behavior (no database needed).

The service must be best-effort: a failing repository insert is logged and
swallowed so auditing can never break the request it observes. Detail text is
also bounded to keep a caller from bloating the log.
"""

from geoavia_backend.services import audit as audit_module
from geoavia_backend.services.audit import AuditService


def test_record_swallows_repository_errors(monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("db down")

    service = AuditService()
    monkeypatch.setattr(service.repo, "insert", _boom)

    # Must not raise even though the underlying insert fails.
    service.record(action="LOGIN", username="alice")


def test_record_truncates_detail(monkeypatch):
    captured: dict = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        return 1

    service = AuditService()
    monkeypatch.setattr(service.repo, "insert", _capture)

    service.record(action="LOGIN", detail="x" * 5000)
    assert len(captured["detail"]) == audit_module._MAX_DETAIL


def test_record_forwards_fields(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        AuditService().repo.__class__, "insert", lambda self, **kw: captured.update(kw) or 1
    )
    service = AuditService()
    service.record(
        action="USER_DELETE",
        user_id=7,
        username="admin1",
        user_role="administrador",
        resource="42",
        detail="Deleted user id 42",
        ip_address="127.0.0.1",
    )
    assert captured["action"] == "USER_DELETE"
    assert captured["user_id"] == 7
    assert captured["resource"] == "42"
