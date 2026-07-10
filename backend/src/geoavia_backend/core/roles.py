"""Centralized role-based access sets.

Single source of truth for the role gates enforced across the API routers.

The system has three roles:
  - operador       : operates the program (maps, analyses, assessments, results,
                     export, screening, shapefile upload). No admin/dev powers.
  - administrador  : everything an operador does, plus user management (create/
                     update/delete users and issue password-recovery codes),
                     layer/source configuration and audit. No developer tools.
  - desenvolvedor  : everything, including developer tools. Governed by APP_ENV
                     (see core.sandbox): in production it is read-only and its
                     write attempts are audited; in sandbox it has full access.
"""

from __future__ import annotations

OPERADOR = "operador"
ADMINISTRADOR = "administrador"
DESENVOLVEDOR = "desenvolvedor"

# All valid role values (used to validate a role before persisting it).
ROLES = {OPERADOR, ADMINISTRADOR, DESENVOLVEDOR}

# Admin-level roles (administrator + developer).
ADMIN_ROLES = {ADMINISTRADOR, DESENVOLVEDOR}

# Any authenticated operational role.
OPERATIONAL_ROLES = {OPERADOR, ADMINISTRADOR, DESENVOLVEDOR}

# --- Endpoint gates (names kept stable for the routers) ---
# Manage users and issue password-recovery codes.
USER_CREATION_ROLES = ADMIN_ROLES
# Configure the fallback data source of a layer.
LAYER_SOURCE_ROLES = ADMIN_ROLES
# Run spatial screening.
SCREENING_ROLES = OPERATIONAL_ROLES
# Trigger Airflow DAGs and read the trigger audit log.
DAG_TRIGGER_ROLES = OPERATIONAL_ROLES
# Upload and read user shapefiles.
SHAPEFILE_UPLOAD_ROLES = OPERATIONAL_ROLES

# Roles an administrator may assign when creating a user. The privileged
# 'desenvolvedor' role can only be granted by another 'desenvolvedor'
# (enforced in the users router).
ALLOWED_ROLES = {OPERADOR, ADMINISTRADOR}
