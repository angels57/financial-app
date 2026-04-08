"""Connection pool for PostgreSQL."""

import logging

from psycopg_pool import ConnectionPool

from app.config.settings import settings

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool | None:
    """Get or create the connection pool. Returns None if db_url is not configured."""
    global _pool  # noqa: PLW0603
    if _pool is not None:
        return _pool
    if not settings.db_url:
        logger.warning("DB_URL not configured — running without database cache")
        return None
    try:
        _pool = ConnectionPool(settings.db_url, min_size=1, max_size=5, open=True)
        return _pool
    except (ConnectionError, OSError):
        logger.exception("Failed to create database connection pool")
        return None
