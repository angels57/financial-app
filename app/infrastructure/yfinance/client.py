"""YFinance client — thin wrapper around yfinance library with optional DB cache."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import pandas as pd
import yfinance as yf

from domain.models import NewsItem, StockInfo
from infrastructure.yfinance.mapper import YFinanceMapper
from infrastructure.yfinance.yfinance_technical_service import YfinanceTechnicalService

if TYPE_CHECKING:
    from db.cache_repo import CacheRepository

logger = logging.getLogger(__name__)

_SOURCE = "yfinance"


class YFinanceClient:
    """Thin client for yfinance — converts raw yfinance data to domain models.

    When a ``cache_repo`` is provided, every fetch follows a read-through
    strategy: return cached data when available, otherwise fetch from yfinance
    and persist the result.
    """

    def __init__(self, ticker: str, *, cache_repo: CacheRepository | None = None):
        self._ticker = ticker
        self._yf = yf.Ticker(ticker)
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
            except Exception:
                logger.debug("Cache read failed for stock_info/%s", self._ticker)

        info = self._mapper.to_stock_info(self._ticker, self._yf.info, self._yf)

        if self._cache:
            try:
                self._cache.upsert_consulted_company(
                    self._ticker, info.short_name, info.sector
                )
                self._cache.upsert_stock_info(self._ticker, info, _SOURCE)
            except Exception:
                logger.debug("Cache write failed for stock_info/%s", self._ticker)

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
            except Exception:
                logger.debug(
                    "Cache read failed for price_history/%s/%s", self._ticker, period
                )

        df = self._yf.history(period=period)

        if self._cache and not df.empty:
            try:
                self._cache.upsert_price_history(self._ticker, period, df, _SOURCE)
            except Exception:
                logger.debug(
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
            except Exception:
                logger.debug("Cache read failed for %s/%s", name, self._ticker)

        try:
            df = fetcher()
        except Exception:
            return None

        if self._cache and df is not None and not df.empty:
            try:
                self._cache.upsert_financial_statement(self._ticker, name, df, _SOURCE)
            except Exception:
                logger.debug("Cache write failed for %s/%s", name, self._ticker)

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
            return annual.to_frame()
        except Exception:
            return None

    # -- News -----------------------------------------------------------------

    def get_news(self, force_refresh: bool = False) -> list[NewsItem]:
        """Fetch news, using DB cache when available."""
        if self._cache and not force_refresh:
            try:
                cached = self._cache.get_news(self._ticker)
                if cached is not None:
                    return cached  # type: ignore[no-any-return]
            except Exception:
                logger.debug("Cache read failed for news/%s", self._ticker)

        try:
            yf_news = self._yf.news
            items: list[NewsItem] = (
                self._mapper.to_news_items(self._ticker, yf_news) if yf_news else []
            )
        except Exception:
            return []

        if self._cache and items:
            try:
                self._cache.upsert_news(self._ticker, items, _SOURCE)
            except Exception:
                logger.debug("Cache write failed for news/%s", self._ticker)

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
                    return cached  # type: ignore[no-any-return]
            except Exception:
                logger.debug("Cache read failed for %s/%s", indicator, self._ticker)

        result = fetcher(self._ticker, interval, time_period)

        if self._cache and result is not None:
            try:
                self._cache.upsert_technical_indicator(
                    self._ticker, indicator, interval, time_period, result, _SOURCE
                )
            except Exception:
                logger.debug("Cache write failed for %s/%s", indicator, self._ticker)

        return result
