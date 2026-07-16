"""Permission catalog and effective-permission resolution.

The three base roles (see ``core.roles``) each grant a fixed permission set.
Custom permission profiles (``mesa_a`` is not used — profiles live in the
default schema alongside ``users``) may grant *additional* permissions on top of
a user's base role. Effective permissions = base-role permissions ∪ profile
permissions.

This keeps the change retro-compatible: a user with no profile behaves exactly
as before (base-role permissions only).
"""

from __future__ import annotations

from geoavia_backend.core.roles import ADMINISTRADOR, DESENVOLVEDOR, OPERADOR

# --- Stable permission catalog (string identifiers) ---
MAP_VIEW = "map:view"
CATALOG_READ = "catalog:read"
SCREENING_RUN = "screening:run"
ANALYSIS_RUN = "analysis:run"
ASSESSMENT_MANAGE = "assessment:manage"
EXPORT_DATA = "export:data"
SHAPEFILE_UPLOAD = "shapefile:upload"
DAG_TRIGGER = "dag:trigger"
ADMIN_USERS = "admin:users"
ADMIN_PROFILES = "admin:profiles"
ADMIN_LAYERS = "admin:layers"
AUDIT_READ = "audit:read"
DEV_TOOLS = "dev:tools"

# All permissions a custom profile is allowed to reference (validation set).
ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        MAP_VIEW,
        CATALOG_READ,
        SCREENING_RUN,
        ANALYSIS_RUN,
        ASSESSMENT_MANAGE,
        EXPORT_DATA,
        SHAPEFILE_UPLOAD,
        DAG_TRIGGER,
        ADMIN_USERS,
        ADMIN_PROFILES,
        ADMIN_LAYERS,
        AUDIT_READ,
        DEV_TOOLS,
    }
)

# Base permissions per role. administrador ⊃ operador; desenvolvedor ⊃ administrador.
_OPERADOR_PERMS = frozenset(
    {
        MAP_VIEW,
        CATALOG_READ,
        SCREENING_RUN,
        ANALYSIS_RUN,
        ASSESSMENT_MANAGE,
        EXPORT_DATA,
        SHAPEFILE_UPLOAD,
        DAG_TRIGGER,
    }
)
_ADMIN_PERMS = _OPERADOR_PERMS | {ADMIN_USERS, ADMIN_PROFILES, ADMIN_LAYERS, AUDIT_READ}
_DEV_PERMS = _ADMIN_PERMS | {DEV_TOOLS}

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    OPERADOR: _OPERADOR_PERMS,
    ADMINISTRADOR: _ADMIN_PERMS,
    DESENVOLVEDOR: _DEV_PERMS,
}


def effective_permissions(role: str, profile_permissions: list[str] | None = None) -> list[str]:
    """Returns the sorted union of a role's base permissions and profile grants."""
    base = ROLE_PERMISSIONS.get(role, frozenset())
    extra = {p for p in (profile_permissions or []) if p in ALL_PERMISSIONS}
    return sorted(base | extra)


def validate_permissions(permissions: list[str]) -> list[str]:
    """Normalizes and validates a permission list, raising ValueError on unknowns."""
    cleaned = []
    seen = set()
    for raw in permissions:
        perm = (raw or "").strip()
        if perm not in ALL_PERMISSIONS:
            raise ValueError(f"Unknown permission: {perm!r}")
        if perm not in seen:
            seen.add(perm)
            cleaned.append(perm)
    return cleaned
