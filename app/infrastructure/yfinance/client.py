"""YFinance client — thin wrapper around yfinance library with optional DB cache."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import pandas as pd
import psycopg
import yfinance as yf
from yfinance.exceptions import YFException

from domain.models import NewsItem, StockInfo
from domain.validators import require_valid_ticker
from infrastructure.yfinance.mapper import YFinanceMapper
from infrastructure.yfinance.yfinance_technical_service import YfinanceTechnicalService

if TYPE_CHECKING:
    from db.cache_repo import CacheRepository

logger = logging.getLogger(__name__)

_SOURCE = "yfinance"

# Exceptions raised by psycopg on any DB interaction.
_CacheError = psycopg.Error


class YFinanceClient:
    """Thin client for yfinance — converts raw yfinance data to domain models.

    When a ``cache_repo`` is provided, every fetch follows a read-through
    strategy: return cached data when available, otherwise fetch from yfinance
    and persist the result.
    """

    def __init__(self, ticker: str, *, cache_repo: CacheRepository | None = None):
        validated: str = require_valid_ticker(ticker)
        self._ticker = validated
        self._yf = yf.Ticker(validated)
        self._mapper = YFinanceMapper()
        self._tech_service = YfinanceTechnicalService()
        self._tech_source = "yfinance"
        self._cache = cache_repo

    def set_technical_source(self, source: str) -> None:
        self._tech_source = source

    @property
    def ticker(self) -> str:
        return self._ticker

    # -- Info -----------------------------------------------------------------

    def get_info(self, force_refresh: bool = False) -> StockInfo:
        """Fetch stock info, using DB cache when available."""
        if self._cache and not force_refresh:
            try:
                cached = self._cache.get_stock_info(self._ticker)
                if cached is not None:
                    return cached
            except _CacheError:
                logger.warning("Cache read failed for stock_info/%s", self._ticker)

        info = self._mapper.to_stock_info(self._ticker, self._yf.info, self._yf)

        if self._cache:
            try:
                self._cache.upsert_consulted_company(
                    self._ticker, info.short_name, info.sector
                )
                self._cache.upsert_stock_info(self._ticker, info, _SOURCE)
            except _CacheError:
                logger.warning("Cache write failed for stock_info/%s", self._ticker)

        return info

    # -- History --------------------------------------------------------------

    def get_history(self, period: str = "1y") -> pd.DataFrame:
        """Fetch price history, using DB cache when available."""
        if self._cache:
            try:
                from config import settings

                cached = self._cache.get_price_history(
                    self._ticker, period, settings.price_cache_ttl_seconds
                )
                if cached is not None:
                    return cached
            except _CacheError:
                logger.warning(
                    "Cache read failed for price_history/%s/%s", self._ticker, period
                )

        df = self._yf.history(period=period)

        if self._cache and not df.empty:
            try:
                self._cache.upsert_price_history(self._ticker, period, df, _SOURCE)
            except _CacheError:
                logger.warning(
                    "Cache write failed for price_history/%s/%s", self._ticker, period
                )

        return df

    # -- Financial statements -------------------------------------------------

    def get_financials(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch income statement."""
        return self._cached_statement(
            "financials", lambda: self._yf.financials, force_refresh
        )

    def get_balance_sheet(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch balance sheet."""
        return self._cached_statement(
            "balance_sheet", lambda: self._yf.balance_sheet, force_refresh
        )

    def get_cashflow(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch cash flow statement."""
        return self._cached_statement(
            "cashflow", lambda: self._yf.cashflow, force_refresh
        )

    def get_quarterly_financials(
        self, force_refresh: bool = False
    ) -> pd.DataFrame | None:
        """Fetch quarterly income statement (used for EPS-vs-price chart)."""
        return self._cached_statement(
            "quarterly_financials",
            lambda: self._yf.quarterly_financials,
            force_refresh,
        )

    def get_eps_series(
        self, frequency: str = "quarterly", force_refresh: bool = False
    ) -> pd.Series | None:
        """Return Diluted EPS series for chart overlay.

        Args:
            frequency: "quarterly" or "annual".
        """
        if frequency == "quarterly":
            df = self.get_quarterly_financials(force_refresh=force_refresh)
        elif frequency == "annual":
            df = self.get_financials(force_refresh=force_refresh)
        else:
            raise ValueError(f"Unknown frequency: {frequency}")

        if df is None or "Diluted EPS" not in df.index:
            return None
        series = df.loc["Diluted EPS"].dropna()
        return series if not series.empty else None

    def _cached_statement(
        self,
        name: str,
        fetcher: Callable[[], pd.DataFrame | None],
        force_refresh: bool,
    ) -> pd.DataFrame | None:
        """Read-through cache for a financial statement."""
        if self._cache and not force_refresh:
            try:
                cached = self._cache.get_financial_statement(self._ticker, name)
                if cached is not None:
                    return cached
            except _CacheError:
                logger.warning("Cache read failed for %s/%s", name, self._ticker)

        try:
            df = fetcher()
        except YFException:
            return None

        if self._cache and df is not None and not df.empty:
            try:
                self._cache.upsert_financial_statement(self._ticker, name, df, _SOURCE)
            except _CacheError:
                logger.warning("Cache write failed for %s/%s", name, self._ticker)

        return df

    # -- Dividends ------------------------------------------------------------

    def get_dividends(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch dividend history, annualized and grouped by year."""
        try:
            df = self._yf.dividends
            if df is None or df.empty:
                return None
            df = df.to_frame(name="Dividend")
            df.index = pd.to_datetime(df.index)
            df["Year"] = df.index.year
            annual = df.groupby("Year")["Dividend"].sum()
            annual = annual.sort_index(ascending=False)
            return annual.to_frame()
        except (YFException, KeyError, ValueError):
            return None

    # -- News -----------------------------------------------------------------

    def get_news(self, force_refresh: bool = False) -> list[NewsItem]:
        """Fetch news, using DB cache when available."""
        if self._cache and not force_refresh:
            try:
                cached = self._cache.get_news(self._ticker)
                if cached is not None:
                    # cache returns list[NewsItem] at runtime; mypy sees loose type from Any
                    return cached  # type: ignore[no-any-return]
            except _CacheError:
                logger.warning("Cache read failed for news/%s", self._ticker)

        try:
            yf_news = self._yf.news
            items: list[NewsItem] = (
                self._mapper.to_news_items(self._ticker, yf_news) if yf_news else []
            )
        except (YFException, KeyError, TypeError):
            return []

        if self._cache and items:
            try:
                self._cache.upsert_news(self._ticker, items, _SOURCE)
            except _CacheError:
                logger.warning("Cache write failed for news/%s", self._ticker)

        return items

    # -- Technical indicators -------------------------------------------------

    def get_sma(
        self,
        time_period: int = 20,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None:
        """Calculate SMA, using DB cache when available."""
        return self._cached_indicator(
            "sma", interval, time_period, force_refresh, self._tech_service.get_sma
        )

    def get_rsi(
        self,
        time_period: int = 14,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None:
        """Calculate RSI, using DB cache when available."""
        return self._cached_indicator(
            "rsi", interval, time_period, force_refresh, self._tech_service.get_rsi
        )

    def get_multiple_sma(
        self,
        periods: list[int] | None = None,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[int, dict[str, float] | None]:
        """Calculate multiple SMAs using local yfinance data."""
        if periods is None:
            periods = [20, 50, 100, 200]
        # service returns compatible but non-identical dict type
        return self._tech_service.get_multiple_sma(self._ticker, interval, periods)  # type: ignore[no-any-return]

    def _cached_indicator(
        self,
        indicator: str,
        interval: str,
        time_period: int,
        force_refresh: bool,
        fetcher: Callable[[str, str, int], dict[str, float] | None],
    ) -> dict[str, float] | None:
        """Read-through cache for a single technical indicator."""
        if self._cache and not force_refresh:
            try:
                from config import settings

                cached = self._cache.get_technical_indicator(
                    self._ticker,
                    indicator,
                    interval,
                    time_period,
                    settings.price_cache_ttl_seconds,
                )
                if cached is not None:
                    # cache returns dict[str,float] at runtime; mypy sees loose type from Any
                    return cached  # type: ignore[no-any-return]
            except _CacheError:
                logger.warning("Cache read failed for %s/%s", indicator, self._ticker)

        result = fetcher(self._ticker, interval, time_period)

        if self._cache and result is not None:
            try:
                self._cache.upsert_technical_indicator(
                    self._ticker, indicator, interval, time_period, result, _SOURCE
                )
            except _CacheError:
                logger.warning("Cache write failed for %s/%s", indicator, self._ticker)

        return result
