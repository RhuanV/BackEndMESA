"""create permission_profiles + users.profile_id (custom profiles — Perfis)

Adds custom permission profiles that grant additional permissions on top of a
user's base role, plus a nullable users.profile_id association. Seeds three
non-deletable system profiles mirroring the base roles (retro-compatible: users
default to profile_id NULL and keep exactly their base-role permissions).

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-15
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS permission_profiles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(60) NOT NULL UNIQUE,
            description VARCHAR(255),
            permissions TEXT[] NOT NULL DEFAULT '{}',
            is_system BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS profile_id INTEGER
            REFERENCES permission_profiles(id) ON DELETE SET NULL;
    """)
    )
    # Seed system profiles mirroring the base roles (idempotent via ON CONFLICT).
    op.execute(
        text("""
        INSERT INTO permission_profiles (name, description, permissions, is_system)
        VALUES
            ('Operador',
             'Perfil base do operador (mapa, análises, exportação).',
             ARRAY['map:view','catalog:read','screening:run','analysis:run',
                   'assessment:manage','export:data','shapefile:upload','dag:trigger'],
             TRUE),
            ('Administrador',
             'Perfil base do administrador (operador + gestão de usuários/camadas/auditoria).',
             ARRAY['map:view','catalog:read','screening:run','analysis:run',
                   'assessment:manage','export:data','shapefile:upload','dag:trigger',
                   'admin:users','admin:profiles','admin:layers','audit:read'],
             TRUE),
            ('Desenvolvedor',
             'Perfil base do desenvolvedor (administrador + ferramentas de dev).',
             ARRAY['map:view','catalog:read','screening:run','analysis:run',
                   'assessment:manage','export:data','shapefile:upload','dag:trigger',
                   'admin:users','admin:profiles','admin:layers','audit:read','dev:tools'],
             TRUE)
        ON CONFLICT (name) DO NOTHING;
    """)
    )


def downgrade() -> None:
    op.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS profile_id;"))
    op.execute(text("DROP TABLE IF EXISTS permission_profiles;"))
