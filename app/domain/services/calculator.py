"""Financial calculator service — pure domain logic."""

from __future__ import annotations

import math

import pandas as pd

from app.domain.models import FinancialMetrics


class FinancialCalculator:
    """Responsabilidad única: calcular métricas financieras a partir de DataFrames."""

    YEARS_LIMIT = 5

    @staticmethod
    def _extract_years(series: pd.Series) -> list[str]:
        return [str(d.year) for d in series.index]

    @staticmethod
    def _calc_growth(series: pd.Series) -> list[float]:
        """Calculate YoY growth. Series is ordered most-recent-first."""
        values = series.values
        growth = []
        for i in range(len(values)):
            if i < len(values) - 1:
                curr, prev = float(values[i]), float(values[i + 1])
                if math.isfinite(curr) and math.isfinite(prev) and prev != 0:
                    growth.append(((curr - prev) / abs(prev)) * 100)
                else:
                    growth.append(0.0)
            else:
                growth.append(0.0)
        return growth

    @staticmethod
    def _calc_ratio(numerator: pd.Series, denominator: pd.Series) -> list[float] | None:
        if len(numerator) != len(denominator):
            return None
        return list(((numerator.values / denominator.values) * 100).tolist())

    def compute(
        self,
        financials: pd.DataFrame | None,
        balance: pd.DataFrame | None,
        cashflow: pd.DataFrame | None,
        pe_ratio: float | None = None,
    ) -> FinancialMetrics:
        metrics = FinancialMetrics(pe_ratio=pe_ratio)
        limit = self.YEARS_LIMIT

        has_revenue = financials is not None and "Total Revenue" in financials.index
        has_net_income = financials is not None and "Net Income" in financials.index
        has_equity = balance is not None and "Stockholders Equity" in balance.index
        has_debt = balance is not None and "Total Debt" in balance.index
        has_fcf = cashflow is not None and "Free Cash Flow" in cashflow.index

        if has_revenue and financials is not None:
            rev = financials.loc["Total Revenue"].iloc[:limit]
            metrics.years = self._extract_years(rev)
            metrics.revenue_billions = list((rev.values / 1e9).tolist())
            metrics.sales_growth = self._calc_growth(rev)

        n_years = len(metrics.years)

        if has_revenue and has_net_income and financials is not None:
            rev = financials.loc["Total Revenue"].iloc[:n_years]
            ni = financials.loc["Net Income"].iloc[:n_years]
            metrics.net_income_billions = list((ni.values / 1e9).tolist())
            metrics.net_margin = list(((ni.values / rev.values) * 100).tolist())

        if (
            has_net_income
            and has_equity
            and financials is not None
            and balance is not None
        ):
            ni = financials.loc["Net Income"].iloc[:n_years]
            equity = balance.loc["Stockholders Equity"].iloc[:n_years]
            roe = self._calc_ratio(ni, equity)
            if roe is not None:
                metrics.roe = roe

        if has_fcf and cashflow is not None:
            fcf = cashflow.loc["Free Cash Flow"].iloc[:n_years]
            metrics.fcf_billions = list((fcf.values / 1e9).tolist())

        if has_net_income and financials is not None:
            ni = financials.loc["Net Income"].iloc[:n_years]
            metrics.eps = list((ni.values / 1e9).tolist())

        if has_debt and balance is not None:
            debt = balance.loc["Total Debt"].iloc[:n_years]
            metrics.debt_billions = list((debt.values / 1e9).tolist())

            if has_equity:
                equity = balance.loc["Stockholders Equity"].iloc[:n_years]
                ratio = self._calc_ratio(debt, equity)
                if ratio is not None:
                    metrics.debt_equity = ratio

        return metrics
