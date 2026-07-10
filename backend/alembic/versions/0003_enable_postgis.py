"""enable postgis extension

Revision ID: 0003
Revises: 0001
Create Date: 2026-07-08
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0003"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))


def downgrade() -> None:
    # Dropping postgis is a destructive global operation that would break all
    # geometry columns — intentionally left as a no-op.
    pass
