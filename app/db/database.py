"""
MuleGuard Central Database Connection & Connection Pool Manager
Provides bounded connection pooling via psycopg_pool.ConnectionPool.
Specifications:
- min_size = 4
- max_size = 20
- Automatic connection return on context exit
- No connection leaks
- Seamless backward compatibility for both `with get_connection() as conn:`
  and `conn = get_connection(); ...; conn.close()`
"""

import os
import atexit
import psycopg
from dotenv import load_dotenv

load_dotenv()

# Build connection parameters from environment
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "muleguard_bank")
DB_USER = os.getenv("DATABASE_USER", "muleguard_app")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

CONNINFO = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

try:
    from psycopg_pool import ConnectionPool
    # Bounded connection pool (min_size=4, max_size=20)
    pool = ConnectionPool(
        conninfo=CONNINFO,
        min_size=4,
        max_size=20,
        open=True,
        close_returns=True,
        timeout=30.0,
        max_idle=600.0,
        max_lifetime=3600.0,
        num_workers=3
    )
    HAS_POOL = True
except Exception:
    pool = None
    HAS_POOL = False

@atexit.register
def _close_pool_on_exit():
    if pool is not None:
        try:
            pool.close()
        except Exception:
            pass


class PooledConnectionContext:
    """
    Transparent context manager and proxy for pooled PostgreSQL connections.
    Guarantees connections are returned to the pool on exit or explicit close.
    """
    __slots__ = ("_pool", "_conn", "_returned")

    def __init__(self, p: ConnectionPool):
        self._pool = p
        self._conn = p.getconn()
        self._returned = False

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                self._conn.rollback()
            except Exception:
                pass
        else:
            try:
                self._conn.commit()
            except Exception:
                pass
        self.close()

    def close(self):
        if not self._returned:
            self._returned = True
            try:
                self._pool.putconn(self._conn)
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_connection():
    """
    Obtains a connection from the pool, or falls back to direct connection.
    Can be used as:
        with get_connection() as conn:
            with conn.cursor() as cur:
                ...
    Or:
        conn = get_connection()
        try:
            ...
        finally:
            conn.close()
    """
    if HAS_POOL and pool is not None:
        return PooledConnectionContext(pool)
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def get_pool():
    """Returns the underlying ConnectionPool instance if available, else None."""
    return pool if (HAS_POOL and pool is not None) else None