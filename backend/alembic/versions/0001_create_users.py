"""create users table

Revision ID: 0001
Revises:
Create Date: 2026-07-08
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            hash TEXT NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'operador',
            CONSTRAINT check_role CHECK (
                role IN ('coordenador', 'gestor', 'supervisor', 'operador', 'administrador', 'desenvolvedor')
            )
        );
    """))
    # Idempotent ADD COLUMN in case this runs on a pre-existing partial schema
    op.execute(text("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'operador';
    """))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS users;"))
