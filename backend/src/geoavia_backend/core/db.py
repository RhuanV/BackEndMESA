"""Database access helper.

`cursor()` centralizes the connect → execute → commit → close cycle used by
every repository (psycopg2's `with connect()` commits but never closes, leaking
connections; this helper closes them).
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from geoavia_backend.core.database import DATABASE_URL


@contextmanager
def cursor(dict_rows: bool = False) -> Iterator:
    """Yields a cursor; commits on success, rolls back on error, always closes.

    `dict_rows=True` yields dict rows (RealDictCursor); otherwise tuple rows.
    """
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=RealDictCursor if dict_rows else None) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
