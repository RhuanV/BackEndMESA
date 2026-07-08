"""Alembic environment configuration for GeoAvia.

Uses raw SQL migrations (no ORM) via op.execute(text(...)). Credentials are
loaded from .env through geoavia_backend.database — they never appear in
alembic.ini or in version control.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Make geoavia_backend importable regardless of working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geoavia_backend.database import SQLALCHEMY_DATABASE_URL  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_online() -> None:
    """Run migrations against the live database.

    NullPool is the Alembic-recommended pool class for migration scripts: it
    opens one connection, runs all pending migrations, then closes it — no
    idle connections left hanging after the script finishes.
    """
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,   # no ORM models — pure raw SQL migrations
            include_schemas=True,   # required: migrations touch the mesa_a schema
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
