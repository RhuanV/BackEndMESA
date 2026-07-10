"""seed demo users (neutralized)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08

This revision used to insert 30 demo users with placeholder (non-loginnable)
hashes. The seed was removed so databases are born empty; the revision is kept
as a no-op to preserve the migration chain (0003 depends on 0002).
"""
from __future__ import annotations

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intentionally empty: demo users are no longer seeded.
    pass


def downgrade() -> None:
    pass
