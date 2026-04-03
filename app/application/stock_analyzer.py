"""Stock analyzer — orchestrates data fetching and metrics computation."""

from __future__ import annotations

import pandas as pd

from domain.models import FinancialMetrics, StockInfo
from domain.services.calculator import FinancialCalculator
from infrastructure.yfinance.client import YFinanceClient


class StockAnalyzer:
    """Orchestrates stock data fetching and financial metrics computation."""

    def __init__(self, yf_client: YFinanceClient):
        self._client = yf_client
        self._calculator = FinancialCalculator()

    @property
    def ticker(self) -> str:
        return self._client.ticker  # type: ignore[no-any-return]

    def get_info(self) -> StockInfo:
        """Fetch stock info from yfinance."""
        return self._client.get_info()

    def get_history(self, period: str = "1y") -> pd.DataFrame:
        """Fetch price history."""
        return self._client.get_history(period)

    def get_financials(self) -> pd.DataFrame | None:
        """Fetch income statement."""
        return self._client.get_financials()

    def get_balance_sheet(self) -> pd.DataFrame | None:
        """Fetch balance sheet."""
        return self._client.get_balance_sheet()

    def get_cashflow(self) -> pd.DataFrame | None:
        """Fetch cash flow statement."""
        return self._client.get_cashflow()

    def get_dividends(self) -> pd.DataFrame | None:
        """Fetch dividend history."""
        return self._client.get_dividends()

    def compute_metrics(
        self,
        financials: pd.DataFrame | None,
        balance: pd.DataFrame | None,
        cashflow: pd.DataFrame | None,
        pe_ratio: float | None = None,
    ) -> FinancialMetrics:
        """Compute financial metrics from raw DataFrames."""
        return self._calculator.compute(
            financials=financials,
            balance=balance,
            cashflow=cashflow,
            pe_ratio=pe_ratio,
        )
