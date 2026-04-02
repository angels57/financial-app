"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


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
