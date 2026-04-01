"""Calculadora de métricas financieras — lógica pura sin dependencias de UI."""

import pandas as pd

from models import FinancialMetrics


class FinancialCalculator:
    """Responsabilidad única: calcular métricas financieras a partir de DataFrames."""

    YEARS_LIMIT = 5

    @staticmethod
    def _extract_years(series: pd.Series) -> list[str]:
        return [str(d.year) for d in series.index]

    @staticmethod
    def _calc_growth(series: pd.Series) -> list[float]:
        growth = []
        prev = None
        for value in series.values:
            if prev:
                growth.append(((value - prev) / prev) * 100)
            else:
                growth.append(0)
            prev = value
        return growth

    @staticmethod
    def _calc_ratio(numerator: pd.Series, denominator: pd.Series) -> list[float] | None:
        if len(numerator) != len(denominator):
            return None
        return ((numerator.values / denominator.values) * 100).tolist()

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

        if has_revenue:
            rev = financials.loc["Total Revenue"].iloc[:limit]
            metrics.years = self._extract_years(rev)
            metrics.revenue_billions = (rev.values / 1e9).tolist()
            metrics.sales_growth = self._calc_growth(rev)

        if has_revenue and has_net_income:
            rev = financials.loc["Total Revenue"].iloc[:limit]
            ni = financials.loc["Net Income"].iloc[:limit]
            metrics.net_income_billions = (ni.values / 1e9).tolist()
            metrics.net_margin = ((ni.values / rev.values) * 100).tolist()

        if has_net_income and has_equity:
            ni = financials.loc["Net Income"].iloc[:limit]
            equity = balance.loc["Stockholders Equity"].iloc[:limit]
            roe = self._calc_ratio(ni, equity)
            if roe is not None:
                metrics.roe = roe

        if has_fcf:
            fcf = cashflow.loc["Free Cash Flow"].iloc[:limit]
            metrics.fcf_billions = (fcf.values / 1e9).tolist()

        if has_debt:
            debt = balance.loc["Total Debt"].iloc[:limit]
            metrics.debt_billions = (debt.values / 1e9).tolist()

            if has_equity:
                equity = balance.loc["Stockholders Equity"].iloc[:limit]
                ratio = self._calc_ratio(debt, equity)
                if ratio is not None:
                    metrics.debt_equity = ratio

        return metrics
