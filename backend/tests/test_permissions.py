"""Pure tests for effective-permission resolution and validation (no DB)."""

import pytest

from geoavia_backend.core.permissions import (
    ADMIN_USERS,
    ANALYSIS_RUN,
    DEV_TOOLS,
    MAP_VIEW,
    effective_permissions,
    validate_permissions,
)
from geoavia_backend.core.roles import ADMINISTRADOR, DESENVOLVEDOR, OPERADOR


def test_operador_base_permissions_exclude_admin():
    perms = effective_permissions(OPERADOR)
    assert MAP_VIEW in perms
    assert ANALYSIS_RUN in perms
    assert ADMIN_USERS not in perms
    assert DEV_TOOLS not in perms


def test_role_hierarchy_is_subset():
    op = set(effective_permissions(OPERADOR))
    adm = set(effective_permissions(ADMINISTRADOR))
    dev = set(effective_permissions(DESENVOLVEDOR))
    assert op < adm < dev
    assert ADMIN_USERS in adm
    assert DEV_TOOLS in dev and DEV_TOOLS not in adm


def test_profile_grants_extra_permissions_on_top_of_role():
    perms = effective_permissions(OPERADOR, [ADMIN_USERS])
    assert ADMIN_USERS in perms  # granted by profile
    assert MAP_VIEW in perms  # still has base-role permissions


def test_unknown_profile_permissions_are_ignored_in_effective():
    perms = effective_permissions(OPERADOR, ["totally:bogus"])
    assert "totally:bogus" not in perms


def test_validate_permissions_dedupes_and_rejects_unknown():
    assert validate_permissions([MAP_VIEW, MAP_VIEW]) == [MAP_VIEW]
    with pytest.raises(ValueError):
        validate_permissions(["nope:nope"])
