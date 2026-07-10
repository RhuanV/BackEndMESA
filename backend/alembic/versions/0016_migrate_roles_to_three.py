"""collapse the role set to three roles

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-09

New role model:
  operador       -> operates the program
  administrador  -> everything an operador does + user management + config + audit
  desenvolvedor  -> everything, sandboxed in production (see core.sandbox)

Legacy roles are mapped:
  coordenador, supervisor, gestor -> administrador
  operador, administrador, desenvolvedor -> unchanged
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;"))

    op.execute(
        text(
            "UPDATE users SET role = 'administrador' "
            "WHERE role IN ('coordenador', 'supervisor', 'gestor');"
        )
    )

    op.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'operador';"))

    op.execute(
        text(
            """
            ALTER TABLE users
            ADD CONSTRAINT check_role
            CHECK (role IN ('operador', 'administrador', 'desenvolvedor'));
            """
        )
    )


def downgrade() -> None:
    # The collapse is lossy (former coordenador/supervisor/gestor cannot be told
    # apart), so we only restore the wider constraint, not the original values.
    op.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role;"))
    op.execute(
        text(
            """
            ALTER TABLE users
            ADD CONSTRAINT check_role
            CHECK (role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador', 'desenvolvedor'));
            """
        )
    )
