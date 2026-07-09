"""Sandbox-mode gating for the developer role (no database needed)."""
from geoavia_backend.core import sandbox


def test_sandbox_env_gives_developer_full_access(monkeypatch):
    monkeypatch.setenv("APP_ENV", "sandbox")
    assert sandbox.is_production() is False
    assert sandbox.developer_write_blocked("desenvolvedor") is False


def test_production_blocks_developer_writes(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert sandbox.is_production() is True
    assert sandbox.developer_write_blocked("desenvolvedor") is True


def test_default_env_is_production(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert sandbox.is_production() is True
    assert sandbox.developer_write_blocked("desenvolvedor") is True


def test_non_developer_roles_are_never_blocked(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    for role in ("administrador", "operador", None):
        assert sandbox.developer_write_blocked(role) is False
