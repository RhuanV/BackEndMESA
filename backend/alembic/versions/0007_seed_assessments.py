"""seed example assessments (neutralized)

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-08

This revision used to insert 5 demo assessments. The seed was removed so
databases are born empty; the revision is kept as a no-op to preserve the
migration chain (0008 depends on 0007).
"""
from __future__ import annotations

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intentionally empty: demo assessments are no longer seeded.
    pass


def downgrade() -> None:
    pass
