"""create audit_log table

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-13
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            username VARCHAR(50),
            user_role VARCHAR(20),
            action VARCHAR(40) NOT NULL,
            resource VARCHAR(120),
            detail TEXT,
            ip_address VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
        ON audit_log (created_at DESC);
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_action
        ON audit_log (action);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS audit_log;"))
