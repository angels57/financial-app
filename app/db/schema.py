"""Database schema initialization."""

import logging

from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS consulted_companies (
    ticker        TEXT PRIMARY KEY,
    short_name    TEXT,
    sector        TEXT DEFAULT '',
    first_queried TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_queried  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stock_info_cache (
    ticker      TEXT PRIMARY KEY REFERENCES consulted_companies(ticker) ON DELETE CASCADE,
    source      TEXT NOT NULL,
    data_json   JSONB NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS price_cache (
    ticker     TEXT NOT NULL REFERENCES consulted_companies(ticker) ON DELETE CASCADE,
    period     TEXT NOT NULL,
    source     TEXT NOT NULL,
    data_json  JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, period)
);

CREATE TABLE IF NOT EXISTS financial_statements_cache (
    ticker       TEXT NOT NULL REFERENCES consulted_companies(ticker) ON DELETE CASCADE,
    statement    TEXT NOT NULL,
    source       TEXT NOT NULL,
    data_json    JSONB NOT NULL,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, statement)
);

CREATE TABLE IF NOT EXISTS news_cache (
    ticker      TEXT NOT NULL REFERENCES consulted_companies(ticker) ON DELETE CASCADE,
    source      TEXT NOT NULL,
    data_json   JSONB NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker)
);

CREATE TABLE IF NOT EXISTS technical_indicators_cache (
    ticker       TEXT NOT NULL,
    indicator    TEXT NOT NULL,
    interval     TEXT NOT NULL,
    time_period  INTEGER NOT NULL,
    data_json    JSONB NOT NULL,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, indicator, interval, time_period)
);
"""


def init_db(pool: ConnectionPool) -> None:
    """Create tables if they don't exist. Idempotent."""
    try:
        with pool.connection() as conn:
            conn.execute(_DDL)
            conn.commit()
        logger.info("Database schema initialized")
    except Exception:
        logger.exception("Failed to initialize database schema")
