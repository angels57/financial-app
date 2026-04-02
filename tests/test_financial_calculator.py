"""Tests for FinancialCalculator - pure business logic."""

import pandas as pd
import pytest

from services import FinancialCalculator


class TestExtractYears:
    """Tests for _extract_years method."""

    def test_extracts_years_from_datetime_index(self):
        dates = pd.to_datetime(["2024-12-31", "2023-12-31", "2022-12-31"])
        series = pd.Series([100, 200, 300], index=dates)
        result = FinancialCalculator._extract_years(series)
        assert result == ["2024", "2023", "2022"]

    def test_handles_single_date(self):
        dates = pd.to_datetime(["2024-12-31"])
        series = pd.Series([100], index=dates)
        result = FinancialCalculator._extract_years(series)
        assert result == ["2024"]


class TestCalcGrowth:
    """Tests for _calc_growth method."""

    def test_calculates_percentage_growth(self):
        series = pd.Series([100, 110, 121, 133.1])
        result = FinancialCalculator._calc_growth(series)
        assert result[0] == 0
        assert result[1] == 10.0
        assert result[2] == 10.0
        assert abs(result[3] - 10.0) < 0.001

    def test_first_value_is_zero(self):
        series = pd.Series([100, 110, 120])
        result = FinancialCalculator._calc_growth(series)
        assert result[0] == 0

    def test_handles_negative_growth(self):
        series = pd.Series([100, 90, 81])
        result = FinancialCalculator._calc_growth(series)
        assert result == [0, -10.0, -10.0]

    def test_handles_single_value(self):
        series = pd.Series([100])
        result = FinancialCalculator._calc_growth(series)
        assert result == [0]


class TestCalcRatio:
    """Tests for _calc_ratio method."""

    def test_calculates_ratio_correctly(self):
        numerator = pd.Series([100, 200, 300])
        denominator = pd.Series([50, 100, 150])
        result = FinancialCalculator._calc_ratio(numerator, denominator)
        assert result == [200.0, 200.0, 200.0]

    def test_returns_none_on_length_mismatch(self):
        numerator = pd.Series([100, 200])
        denominator = pd.Series([50, 100, 150])
        result = FinancialCalculator._calc_ratio(numerator, denominator)
        assert result is None

    def test_returns_empty_list_on_empty_series(self):
        numerator = pd.Series([], dtype=float)
        denominator = pd.Series([], dtype=float)
        result = FinancialCalculator._calc_ratio(numerator, denominator)
        assert result == []


class TestCompute:
    """Tests for compute method - main calculation entry point."""

    def test_computes_revenue_and_growth(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
            pe_ratio=25.0,
        )

        assert len(metrics.years) == 5
        assert metrics.years[0] == "2024"
        assert len(metrics.revenue_billions) == 5
        assert metrics.revenue_billions[0] == 500.0
        assert metrics.pe_ratio == 25.0

    def test_computes_net_margin(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.net_margin) == 5
        assert metrics.net_margin[0] == 10.0

    def test_computes_roe(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.roe) == 5
        assert metrics.roe[0] == 25.0

    def test_computes_fcf(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.fcf_billions) == 5
        assert metrics.fcf_billions[0] == 30.0

    def test_computes_debt_equity(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.debt_equity) == 5
        assert metrics.debt_equity[0] == 50.0

    def test_handles_none_financials(self, sample_balance_data, sample_cashflow_data):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=None,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert metrics.years == []
        assert metrics.revenue_billions == []

    def test_handles_empty_financials(
        self, empty_financials, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=empty_financials,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert metrics.years == []
        assert metrics.revenue_billions == []

    def test_handles_partial_balance_without_debt(
        self, sample_financials_data, partial_balance_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=partial_balance_data,
            cashflow=None,
        )

        assert metrics.debt_billions == []
        assert metrics.debt_equity == []

    def test_calculates_sales_growth(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.sales_growth) == 5
        assert metrics.sales_growth[0] == 0
        assert metrics.sales_growth[1] == pytest.approx(-10.0, rel=0.01)

    def test_years_limit_applied(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.years) == 5
        assert calculator.YEARS_LIMIT == 5

    def test_net_income_billions_calculated(
        self, sample_financials_data, sample_balance_data, sample_cashflow_data
    ):
        calculator = FinancialCalculator()
        metrics = calculator.compute(
            financials=sample_financials_data,
            balance=sample_balance_data,
            cashflow=sample_cashflow_data,
        )

        assert len(metrics.net_income_billions) == 5
        assert metrics.net_income_billions[0] == 50.0
