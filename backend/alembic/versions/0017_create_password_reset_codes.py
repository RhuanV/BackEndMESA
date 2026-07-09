"""create password_reset_codes for admin-issued recovery codes

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-09

Stores single-use, time-limited password recovery codes. Only the hash of each
code is persisted; see services.password_reset for the flow.
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS password_reset_codes (
                id          serial PRIMARY KEY,
                user_id     integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                code_hash   text NOT NULL,
                attempts    integer NOT NULL DEFAULT 0,
                expires_at  timestamptz NOT NULL,
                used_at     timestamptz,
                created_by  integer REFERENCES users(id) ON DELETE SET NULL,
                created_at  timestamptz NOT NULL DEFAULT now()
            );
            """
        )
    )
    # Speeds up the "active code for this user" lookup during a reset.
    op.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_prc_user_active "
            "ON password_reset_codes (user_id) WHERE used_at IS NULL;"
        )
    )


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS password_reset_codes;"))
