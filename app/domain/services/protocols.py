"""Protocols (interfaces) for service layer — enables structural subtyping without inheritance."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd

from models import NewsItem, StockInfo


@runtime_checkable
class StockDataFetcherProtocol(Protocol):
    """Minimal protocol for fetching basic stock data."""

    @property
    def ticker(self) -> str:
        """Ticker symbol."""
        ...

    def get_info(self, force_refresh: bool = False) -> StockInfo:
        """Fetch stock info."""
        ...

    def get_history(self, period: str) -> pd.DataFrame:
        """Fetch price history."""
        ...

    def get_financials(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch income statement."""
        ...

    def get_balance_sheet(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch balance sheet."""
        ...

    def get_cashflow(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch cash flow statement."""
        ...

    def get_quarterly_financials(
        self, force_refresh: bool = False
    ) -> pd.DataFrame | None:
        """Fetch quarterly income statement."""
        ...

    def get_eps_series(
        self, frequency: str = "quarterly", force_refresh: bool = False
    ) -> pd.Series | None:
        """Return Diluted EPS series (quarterly or annual)."""
        ...

    def get_dividends(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch dividend history."""
        ...

    def get_news(self, force_refresh: bool = False) -> list[NewsItem]:
        """Fetch news items."""
        ...


@runtime_checkable
class TechnicalIndicatorFetcherProtocol(Protocol):
    """Protocol for fetching technical indicators (SMA, RSI)."""

    def get_sma(
        self,
        time_period: int = 20,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None: ...

    def get_multiple_sma(
        self,
        periods: list[int] | None = None,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[int, dict[str, float] | None]: ...

    def get_rsi(
        self,
        time_period: int = 14,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None: ...

    def set_technical_source(self, source: str) -> None: ...


StockServiceProtocol = StockDataFetcherProtocol
"""Alias for StockDataFetcherProtocol — kept for backward compatibility."""


@runtime_checkable
class StockDataServiceProtocol(Protocol):
    """Combined protocol for stock data + technical indicators (DataAggregator)."""

    @property
    def ticker(self) -> str: ...

    def get_info(self, force_refresh: bool = False) -> StockInfo: ...

    def get_history(self, period: str) -> pd.DataFrame: ...

    def get_financials(self, force_refresh: bool = False) -> pd.DataFrame | None: ...

    def get_balance_sheet(self, force_refresh: bool = False) -> pd.DataFrame | None: ...

    def get_cashflow(self, force_refresh: bool = False) -> pd.DataFrame | None: ...

    def get_quarterly_financials(
        self, force_refresh: bool = False
    ) -> pd.DataFrame | None: ...

    def get_eps_series(
        self, frequency: str = "quarterly", force_refresh: bool = False
    ) -> pd.Series | None: ...

    def get_dividends(self, force_refresh: bool = False) -> pd.DataFrame | None: ...

    def get_news(self, force_refresh: bool = False) -> list[NewsItem]: ...

    def get_sma(
        self,
        time_period: int = 20,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None: ...

    def get_multiple_sma(
        self,
        periods: list[int] | None = None,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[int, dict[str, float] | None]: ...

    def get_rsi(
        self,
        time_period: int = 14,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None: ...

    def set_technical_source(self, source: str) -> None: ...
