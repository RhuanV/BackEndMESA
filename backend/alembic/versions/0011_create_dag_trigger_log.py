"""create dag_trigger_log audit table

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-08
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
        CREATE TABLE IF NOT EXISTS dag_trigger_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            username VARCHAR(50) NOT NULL,
            user_role VARCHAR(20) NOT NULL,
            dag_id VARCHAR(100) NOT NULL,
            dag_run_id VARCHAR(255),
            status VARCHAR(20) NOT NULL DEFAULT 'triggered'
                CHECK (status IN ('triggered', 'failed_to_trigger')),
            error_message TEXT,
            triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_dag_trigger_log_dag_id
        ON dag_trigger_log (dag_id);
    """)
    )
    op.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_dag_trigger_log_triggered_at
        ON dag_trigger_log (triggered_at DESC);
    """)
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS dag_trigger_log;"))
