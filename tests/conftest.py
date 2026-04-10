"""Pytest configuration and shared fixtures."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from db.cache_repo import CacheRepository


@pytest.fixture
def sample_financials_data() -> pd.DataFrame:
    """Sample financials DataFrame for testing.

    DataFrame structure matches yfinance:
    - index: metric names
    - columns: dates (as datetime)
    """
    dates = pd.to_datetime(
        ["2024-12-31", "2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"]
    )
    data = {
        "Total Revenue": [5.00e11, 4.50e11, 4.00e11, 3.80e11, 3.50e11],
        "Net Income": [5.00e10, 4.50e10, 4.00e10, 3.50e10, 3.00e10],
    }
    return pd.DataFrame(data, index=dates).T


@pytest.fixture
def sample_balance_data() -> pd.DataFrame:
    """Sample balance sheet DataFrame for testing."""
    dates = pd.to_datetime(
        ["2024-12-31", "2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"]
    )
    data = {
        "Stockholders Equity": [2.00e11, 1.80e11, 1.60e11, 1.40e11, 1.20e11],
        "Total Debt": [1.00e11, 9.00e10, 8.00e10, 7.00e10, 6.00e10],
    }
    return pd.DataFrame(data, index=dates).T


@pytest.fixture
def sample_cashflow_data() -> pd.DataFrame:
    """Sample cashflow DataFrame for testing."""
    dates = pd.to_datetime(
        ["2024-12-31", "2023-12-31", "2022-12-31", "2021-12-31", "2020-12-31"]
    )
    data = {
        "Free Cash Flow": [3.00e10, 2.50e10, 2.00e10, 1.80e10, 1.50e10],
    }
    return pd.DataFrame(data, index=dates).T


@pytest.fixture
def empty_financials() -> pd.DataFrame:
    """Empty financials DataFrame for testing edge cases."""
    return pd.DataFrame()


@pytest.fixture
def partial_balance_data() -> pd.DataFrame:
    """Balance sheet with only equity (no debt) for testing."""
    dates = pd.to_datetime(["2024-12-31", "2023-12-31", "2022-12-31"])
    data = {
        "Stockholders Equity": [2.00e11, 1.80e11, 1.60e11],
    }
    return pd.DataFrame(data, index=dates).T


class FakeCacheRepository:
    """In-memory fake implementing CacheRepository protocol for testing."""

    def __init__(self) -> None:
        self._stock_info: dict[str, Any] = {}
        self._price_history: dict[tuple[str, str], tuple[datetime, Any]] = {}
        self._financial_statements: dict[tuple[str, str], Any] = {}
        self._news: dict[str, Any] = {}
        self._technical_indicators: dict[
            tuple[str, str, str, int], tuple[datetime, Any]
        ] = {}
        self._consulted_companies: list[dict] = []

    def upsert_consulted_company(
        self, ticker: str, short_name: str, sector: str
    ) -> None:
        self._consulted_companies = [
            c for c in self._consulted_companies if c["ticker"] != ticker
        ]
        self._consulted_companies.append(
            {
                "ticker": ticker,
                "short_name": short_name,
                "sector": sector,
                "last_queried": datetime.now(timezone.utc),
            }
        )

    def get_consulted_companies(self) -> list[dict]:
        return sorted(self._consulted_companies, key=lambda c: c["last_queried"])

    def get_stock_info(self, ticker: str) -> Any:
        return self._stock_info.get(ticker)

    def upsert_stock_info(self, ticker: str, info: Any, source: str) -> None:
        self._stock_info[ticker] = info

    def get_price_history(self, ticker: str, period: str, max_age_seconds: int) -> Any:
        key = (ticker, period)
        entry = self._price_history.get(key)
        if entry is None:
            return None
        fetched_at, df = entry
        age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
        if age > max_age_seconds:
            return None
        return df

    def upsert_price_history(
        self, ticker: str, period: str, df: Any, source: str
    ) -> None:
        self._price_history[(ticker, period)] = (
            datetime.now(timezone.utc),
            df,
        )

    def get_financial_statement(self, ticker: str, statement: str) -> Any:
        return self._financial_statements.get((ticker, statement))

    def upsert_financial_statement(
        self, ticker: str, statement: str, df: Any, source: str
    ) -> None:
        self._financial_statements[(ticker, statement)] = df

    def get_news(self, ticker: str) -> Any:
        return self._news.get(ticker)

    def upsert_news(self, ticker: str, news: Any, source: str) -> None:
        self._news[ticker] = news

    def get_technical_indicator(
        self,
        ticker: str,
        indicator: str,
        interval: str,
        time_period: int,
        max_age_seconds: int,
    ) -> Any:
        key = (ticker, indicator, interval, time_period)
        entry = self._technical_indicators.get(key)
        if entry is None:
            return None
        fetched_at, data = entry
        age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
        if age > max_age_seconds:
            return None
        return data

    def upsert_technical_indicator(
        self,
        ticker: str,
        indicator: str,
        interval: str,
        time_period: int,
        data: Any,
        source: str,
    ) -> None:
        self._technical_indicators[(ticker, indicator, interval, time_period)] = (
            datetime.now(timezone.utc),
            data,
        )


@pytest.fixture
def fake_cache_repo() -> CacheRepository:  # type: ignore[override]
    """In-memory fake CacheRepository for unit testing without a DB."""
    return FakeCacheRepository()


@pytest.fixture
def mock_yf_ticker() -> MagicMock:
    """MagicMock simulating a yfinance.Ticker object."""
    mock = MagicMock()
    dates_idx = pd.to_datetime(["2024-12-31", "2023-12-31", "2022-12-31"])

    mock.info = {
        "shortName": "Apple Inc.",
        "sector": "Technology",
        "currentPrice": 250.0,
        "trailingAnnualDividendRate": 1.0,
        "dividendYield": 0.004,
    }
    mock.history.return_value = pd.DataFrame(
        {"Close": [250, 240, 230], "Volume": [1e6, 1.1e6, 1.2e6]},
        index=dates_idx,
    )
    mock.financials = pd.DataFrame(
        {
            "Total Revenue": [5.00e11, 4.50e11, 4.00e11],
            "Net Income": [5.00e10, 4.50e10, 4.00e10],
        },
        index=dates_idx,
    )
    mock.balance_sheet = pd.DataFrame(
        {
            "Stockholders Equity": [2.00e11, 1.80e11, 1.60e11],
            "Total Debt": [1.00e11, 9.00e10, 8.00e10],
        },
        index=dates_idx,
    )
    mock.cashflow = pd.DataFrame(
        {"Free Cash Flow": [3.00e10, 2.50e10, 2.00e10]},
        index=dates_idx,
    )
    mock.dividends = pd.Series(
        [0.25, 0.24, 0.23, 0.22],
        index=pd.to_datetime(["2024-12-15", "2024-09-15", "2024-06-15", "2024-03-15"]),
    )
    mock.news = [
        {
            "content": {
                "title": "Apple reports record earnings",
                "canonicalUrl": {"url": "https://example.com/news/1"},
                "provider": {"displayName": "Reuters"},
                "pubDate": "2024-12-15T10:00:00Z",
                "thumbnail": {"resolutions": [{"url": "https://example.com/img.jpg"}]},
            }
        }
    ]
    return mock
