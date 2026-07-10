"""RBAC role-set invariants (no database needed)."""

from geoavia_backend.core import roles


def test_exactly_three_roles():
    assert roles.ROLES == {"operador", "administrador", "desenvolvedor"}


def test_every_gate_is_a_subset_of_roles():
    for gate in (
        roles.USER_CREATION_ROLES,
        roles.LAYER_SOURCE_ROLES,
        roles.SCREENING_ROLES,
        roles.DAG_TRIGGER_ROLES,
        roles.SHAPEFILE_UPLOAD_ROLES,
        roles.ALLOWED_ROLES,
    ):
        assert gate <= roles.ROLES


def test_admin_only_gates_exclude_operador():
    assert "operador" not in roles.USER_CREATION_ROLES
    assert "operador" not in roles.LAYER_SOURCE_ROLES
    assert roles.USER_CREATION_ROLES == {"administrador", "desenvolvedor"}


def test_operational_gates_include_all_three():
    assert roles.SCREENING_ROLES == roles.ROLES
    assert roles.SHAPEFILE_UPLOAD_ROLES == roles.ROLES
    assert roles.DAG_TRIGGER_ROLES == roles.ROLES


def test_desenvolvedor_not_self_service_assignable():
    # Granting 'desenvolvedor' is restricted (handled in the users router).
    assert "desenvolvedor" not in roles.ALLOWED_ROLES
