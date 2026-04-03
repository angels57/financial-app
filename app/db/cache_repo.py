"""Cache repository for reading/writing financial data in PostgreSQL."""

import json
import logging
from datetime import datetime, timezone
from io import StringIO

import pandas as pd
from psycopg_pool import ConnectionPool

from models import NewsItem, StockInfo

logger = logging.getLogger(__name__)


class CacheRepository:
    """Reads and writes cached financial data to PostgreSQL."""

    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    # -- Consulted Companies --------------------------------------------------

    def upsert_consulted_company(
        self, ticker: str, short_name: str, sector: str
    ) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO consulted_companies (ticker, short_name, sector)
                VALUES (%s, %s, %s)
                ON CONFLICT (ticker) DO UPDATE
                SET short_name = EXCLUDED.short_name,
                    sector = EXCLUDED.sector,
                    last_queried = now()
                """,
                (ticker, short_name, sector),
            )
            conn.commit()

    def get_consulted_companies(self) -> list[dict]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                "SELECT ticker, short_name, sector, last_queried "
                "FROM consulted_companies ORDER BY last_queried DESC LIMIT 20"
            ).fetchall()
        return [
            {
                "ticker": r[0],
                "short_name": r[1],
                "sector": r[2],
                "last_queried": r[3],
            }
            for r in rows
        ]

    # -- StockInfo Cache ------------------------------------------------------

    def get_stock_info(self, ticker: str) -> StockInfo | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT data_json FROM stock_info_cache WHERE ticker = %s",
                (ticker,),
            ).fetchone()
        if row is None:
            return None
        return StockInfo.model_validate_json(json.dumps(row[0]))

    def upsert_stock_info(self, ticker: str, info: StockInfo, source: str) -> None:
        data = info.model_dump_json()
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO stock_info_cache (ticker, source, data_json)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (ticker) DO UPDATE
                SET source = EXCLUDED.source,
                    data_json = EXCLUDED.data_json,
                    fetched_at = now()
                """,
                (ticker, source, data),
            )
            conn.commit()

    # -- Price History Cache --------------------------------------------------

    def get_price_history(
        self, ticker: str, period: str, max_age_seconds: int
    ) -> pd.DataFrame | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT data_json, fetched_at FROM price_cache "
                "WHERE ticker = %s AND period = %s",
                (ticker, period),
            ).fetchone()
        if row is None:
            return None
        fetched_at = row[1]
        age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
        if age > max_age_seconds:
            return None
        return pd.read_json(StringIO(json.dumps(row[0])))

    def upsert_price_history(
        self, ticker: str, period: str, df: pd.DataFrame, source: str
    ) -> None:
        data = df.to_json(date_format="iso")
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO price_cache (ticker, period, source, data_json)
                VALUES (%s, %s, %s, %s::jsonb)
                ON CONFLICT (ticker, period) DO UPDATE
                SET source = EXCLUDED.source,
                    data_json = EXCLUDED.data_json,
                    fetched_at = now()
                """,
                (ticker, period, source, data),
            )
            conn.commit()

    # -- Financial Statements Cache -------------------------------------------

    def get_financial_statement(
        self, ticker: str, statement: str
    ) -> pd.DataFrame | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT data_json FROM financial_statements_cache "
                "WHERE ticker = %s AND statement = %s",
                (ticker, statement),
            ).fetchone()
        if row is None:
            return None
        return pd.read_json(StringIO(json.dumps(row[0])))

    def upsert_financial_statement(
        self, ticker: str, statement: str, df: pd.DataFrame, source: str
    ) -> None:
        data = df.to_json(date_format="iso")
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO financial_statements_cache (ticker, statement, source, data_json)
                VALUES (%s, %s, %s, %s::jsonb)
                ON CONFLICT (ticker, statement) DO UPDATE
                SET source = EXCLUDED.source,
                    data_json = EXCLUDED.data_json,
                    fetched_at = now()
                """,
                (ticker, statement, source, data),
            )
            conn.commit()

    # -- News Cache -----------------------------------------------------------

    def get_news(self, ticker: str) -> list[NewsItem] | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT data_json FROM news_cache WHERE ticker = %s",
                (ticker,),
            ).fetchone()
        if row is None:
            return None
        items = row[0]
        return [NewsItem.model_validate(item) for item in items]

    def upsert_news(self, ticker: str, news: list[NewsItem], source: str) -> None:
        data = json.dumps([item.model_dump() for item in news])
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO news_cache (ticker, source, data_json)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (ticker) DO UPDATE
                SET source = EXCLUDED.source,
                    data_json = EXCLUDED.data_json,
                    fetched_at = now()
                """,
                (ticker, source, data),
            )
            conn.commit()

    def get_technical_indicator(
        self,
        ticker: str,
        indicator: str,
        interval: str,
        time_period: int,
        max_age_seconds: int,
    ) -> dict[str, float] | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT data_json, fetched_at FROM technical_indicators_cache "
                "WHERE ticker = %s AND indicator = %s AND interval = %s AND time_period = %s",
                (ticker, indicator, interval, time_period),
            ).fetchone()
        if row is None:
            return None
        fetched_at = row[1]
        age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
        if age > max_age_seconds:
            return None
        # psycopg2 row index is untyped; value is cached JSON dict[str,float]
        return row[0]  # type: ignore[no-any-return]

    def upsert_technical_indicator(
        self,
        ticker: str,
        indicator: str,
        interval: str,
        time_period: int,
        data: dict[str, float],
        source: str,
    ) -> None:
        data_json = json.dumps(data)
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO technical_indicators_cache (ticker, indicator, interval, time_period, data_json)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (ticker, indicator, interval, time_period) DO UPDATE
                SET data_json = EXCLUDED.data_json,
                    fetched_at = now()
                """,
                (ticker, indicator, interval, time_period, data_json),
            )
            conn.commit()
