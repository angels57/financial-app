"""YFinance client — thin wrapper around yfinance library."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from domain.models import NewsItem, StockInfo
from infrastructure.yfinance.mapper import YFinanceMapper


class YFinanceClient:
    """Thin client for yfinance — converts raw yfinance data to domain models."""

    def __init__(self, ticker: str):
        self._ticker = ticker
        self._yf = yf.Ticker(ticker)
        self._mapper = YFinanceMapper()

    @property
    def ticker(self) -> str:
        return self._ticker

    def get_info(self, force_refresh: bool = False) -> StockInfo:
        """Fetch stock info and convert to domain model."""
        yf_info = self._yf.info
        return self._mapper.to_stock_info(self._ticker, yf_info, self._yf)

    def get_history(self, period: str = "1y") -> pd.DataFrame:
        """Fetch price history."""
        return self._yf.history(period=period)

    def get_financials(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch income statement."""
        try:
            return self._yf.financials
        except Exception:
            return None

    def get_balance_sheet(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch balance sheet."""
        try:
            return self._yf.balance_sheet
        except Exception:
            return None

    def get_cashflow(self, force_refresh: bool = False) -> pd.DataFrame | None:
        """Fetch cash flow statement."""
        try:
            return self._yf.cashflow
        except Exception:
            return None

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

    def get_news(self, force_refresh: bool = False) -> list[NewsItem]:
        """Fetch news and convert to domain models."""
        try:
            yf_news = self._yf.news
            if yf_news:
                return self._mapper.to_news_items(self._ticker, yf_news)  # type: ignore[no-any-return]
        except Exception:
            pass
        return []  # type: ignore[no-any-return]
