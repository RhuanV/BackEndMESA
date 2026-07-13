"""create processing_log table

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-13
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS processing_log (
            id SERIAL PRIMARY KEY,
            job VARCHAR(120) NOT NULL,
            layer VARCHAR(120),
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('completed', 'processing', 'failed')),
            duration_ms INTEGER,
            detail TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_processing_log_created_at
        ON processing_log (created_at DESC);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS processing_log;"))
