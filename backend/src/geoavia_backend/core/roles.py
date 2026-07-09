"""Centralized role-based access sets.

Single source of truth for the role gates enforced across the API routers,
replacing the constants that were previously scattered through main.py.
"""
from __future__ import annotations

# Roles allowed to be assigned when registering a user (UserService validation).
ALLOWED_ROLES = {"coordenador", "operador", "administrador"}

# Endpoint gates.
USER_CREATION_ROLES = {"coordenador", "supervisor", "desenvolvedor"}
LAYER_SOURCE_ROLES = {"coordenador", "administrador"}
SCREENING_ROLES = {"coordenador", "gestor", "operador", "administrador", "desenvolvedor"}
DAG_TRIGGER_ROLES = {"coordenador", "operador", "administrador", "desenvolvedor"}
SHAPEFILE_UPLOAD_ROLES = {"coordenador", "operador", "administrador"}
