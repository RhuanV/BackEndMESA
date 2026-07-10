"""Database access helper.

`cursor()` centralizes the connect → execute → commit → close cycle used by
every repository. Connections come from a lazily-initialized thread-safe pool so
concurrent requests reuse a bounded set of connections instead of opening a new
one per query.
"""
from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor

from geoavia_backend.core.database import DATABASE_URL

_POOL_MIN = 1
_POOL_MAX = 10

_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    """Returns the process-wide connection pool, creating it on first use."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pg_pool.ThreadedConnectionPool(
                    _POOL_MIN, _POOL_MAX, dsn=DATABASE_URL
                )
    return _pool


@contextmanager
def cursor(dict_rows: bool = False) -> Iterator:
    """Yields a cursor; commits on success, rolls back on error, always returns
    the connection to the pool.

    `dict_rows=True` yields dict rows (RealDictCursor); otherwise tuple rows. A
    connection that errored is closed instead of being returned to the pool, so
    a broken socket never gets reused.
    """
    pool = _get_pool()
    conn = pool.getconn()
    broken = False
    try:
        with conn.cursor(cursor_factory=RealDictCursor if dict_rows else None) as cur:
            yield cur
        conn.commit()
    except Exception:
        broken = True
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        pool.putconn(conn, close=broken)
