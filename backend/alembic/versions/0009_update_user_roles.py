"""migrate legacy roles to Sprint 3 MESA-A role set

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-08

Maps old roles:
  analyst -> operador
  admin   -> coordenador
  dev     -> administrador
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint so we can rename roles safely
    op.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;"))

    op.execute(text("UPDATE users SET role = 'operador'    WHERE role = 'analyst';"))
    op.execute(text("UPDATE users SET role = 'coordenador' WHERE role = 'admin';"))
    op.execute(text("UPDATE users SET role = 'administrador' WHERE role = 'dev';"))

    op.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'operador';"))

    op.execute(text("""
        ALTER TABLE users
        ADD CONSTRAINT check_role
        CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador', 'desenvolvedor'));
    """))


def downgrade() -> None:
    op.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;"))

    op.execute(text("UPDATE users SET role = 'analyst'      WHERE role = 'operador';"))
    op.execute(text("UPDATE users SET role = 'admin'        WHERE role = 'coordenador';"))
    op.execute(text("UPDATE users SET role = 'dev'          WHERE role = 'administrador';"))

    op.execute(text("""
        ALTER TABLE users
        ADD CONSTRAINT check_role
        CHECK (role IN ('analyst', 'admin', 'dev'));
    """))
