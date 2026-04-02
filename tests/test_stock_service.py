"""Tests for StockService - yfinance data fetching."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from models import StockInfo
from services import StockService


@pytest.fixture
def mock_yfinance_ticker():
    """Create a mock yfinance Ticker object."""
    with patch("services.stock_service.yf.Ticker") as mock_ticker:
        yield mock_ticker


@pytest.fixture
def mock_stock_info():
    """Sample StockInfo for testing."""
    return StockInfo(
        ticker="AAPL",
        short_name="Apple Inc.",
        price=175.50,
        currency="USD",
        market_cap=2.8e12,
        pe_ratio=28.5,
        volume=45_000_000,
    )


class TestStockServiceInit:
    """Tests for StockService initialization."""

    def test_ticker_property(self):
        service = StockService("AAPL")
        assert service.ticker == "AAPL"

    def test_ticker_symbol_set_correctly(self):
        service = StockService("MSFT")
        assert service._ticker_symbol == "MSFT"


class TestGetInfo:
    """Tests for get_info method."""

    def test_get_info_returns_stock_info(self, mock_yfinance_ticker):
        mock_info = MagicMock()
        mock_info.fast_info.last_price = 175.50
        mock_info.fast_info.currency = "USD"
        mock_info.fast_info.market_cap = 2.8e12
        mock_info.fast_info.last_volume = 45_000_000
        mock_info.info = {
            "shortName": "Apple Inc.",
            "trailingPE": 28.5,
            "fiftyTwoWeekLow": 164.00,
            "fiftyTwoWeekHigh": 199.00,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "United States",
            "fullTimeEmployees": 164000,
            "website": "https://apple.com",
            "longBusinessSummary": "Apple Inc. description",
            "beta": 1.2,
            "dividendYield": 0.005,
            "trailingEps": 6.13,
            "targetMeanPrice": 210.00,
            "recommendationKey": "buy",
            "sharesOutstanding": 15_500_000_000,
            "forwardPE": 24.0,
            "priceToSalesTrailing12Months": 7.5,
            "freeCashflow": 100e9,
            "totalRevenue": 394e9,
            "netIncomeToCommon": 97e9,
        }
        mock_yfinance_ticker.return_value = mock_info

        with patch(
            "services.stock_service._fetch_info",
            return_value=StockInfo(
                ticker="AAPL",
                short_name="Apple Inc.",
                price=175.50,
                currency="USD",
            ),
        ):
            service = StockService("AAPL")
            info = service.get_info()
            assert info.ticker == "AAPL"


class TestGetHistory:
    """Tests for get_history method."""

    def test_get_history_returns_dataframe(self, mock_yfinance_ticker):
        mock_history = pd.DataFrame({"Close": [175.0, 176.0, 177.0]})
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = mock_history
        mock_yfinance_ticker.return_value = mock_ticker_instance

        service = StockService("AAPL")
        with patch("services.stock_service._fetch_history", return_value=mock_history):
            result = service.get_history("1mo")
            assert isinstance(result, pd.DataFrame)


class TestGetFinancials:
    """Tests for get_financials method."""

    def test_get_financials_returns_dataframe(self, mock_yfinance_ticker):
        mock_financials = pd.DataFrame(
            {
                "Total Revenue": [500e9, 450e9],
                "Net Income": [50e9, 45e9],
            }
        )
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.financials = mock_financials
        mock_yfinance_ticker.return_value = mock_ticker_instance

        service = StockService("AAPL")
        with patch(
            "services.stock_service._fetch_financials", return_value=mock_financials
        ):
            result = service.get_financials()
            assert isinstance(result, pd.DataFrame)

    def test_get_financials_returns_none_when_empty(self, mock_yfinance_ticker):
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.financials = pd.DataFrame()
        mock_yfinance_ticker.return_value = mock_ticker_instance

        service = StockService("AAPL")
        with patch("services.stock_service._fetch_financials", return_value=None):
            result = service.get_financials()
            assert result is None


class TestGetBalanceSheet:
    """Tests for get_balance_sheet method."""

    def test_get_balance_sheet_returns_dataframe(self, mock_yfinance_ticker):
        mock_balance = pd.DataFrame(
            {
                "Stockholders Equity": [200e9, 180e9],
                "Total Debt": [100e9, 90e9],
            }
        )
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.balance_sheet = mock_balance
        mock_yfinance_ticker.return_value = mock_ticker_instance

        service = StockService("AAPL")
        with patch(
            "services.stock_service._fetch_balance_sheet", return_value=mock_balance
        ):
            result = service.get_balance_sheet()
            assert isinstance(result, pd.DataFrame)


class TestGetCashflow:
    """Tests for get_cashflow method."""

    def test_get_cashflow_returns_dataframe(self, mock_yfinance_ticker):
        mock_cashflow = pd.DataFrame(
            {
                "Free Cash Flow": [30e9, 25e9],
            }
        )
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.cashflow = mock_cashflow
        mock_yfinance_ticker.return_value = mock_ticker_instance

        service = StockService("AAPL")
        with patch(
            "services.stock_service._fetch_cashflow", return_value=mock_cashflow
        ):
            result = service.get_cashflow()
            assert isinstance(result, pd.DataFrame)


class TestGetNews:
    """Tests for get_news method."""

    def test_get_news_returns_news_items(self):
        mock_news = [
            {
                "content": {
                    "title": "Apple reports earnings",
                    "clickThroughUrl": {"url": "https://example.com/news/1"},
                    "provider": {"displayName": "Reuters"},
                    "thumbnail": {
                        "resolutions": [{"url": "https://example.com/thumb.jpg"}]
                    },
                    "pubDate": "2024-01-15T09:00:00Z",
                }
            }
        ]

        with patch("services.stock_service._fetch_news", return_value=mock_news):
            service = StockService("AAPL")
            news = service.get_news()
            assert len(news) == 1
            assert news[0].title == "Apple reports earnings"
            assert news[0].link == "https://example.com/news/1"
            assert news[0].publisher == "Reuters"

    def test_get_news_returns_empty_on_error(self):
        with patch("services.stock_service._fetch_news", return_value=[]):
            service = StockService("AAPL")
            news = service.get_news()
            assert news == []

    def test_get_news_handles_missing_fields(self):
        mock_news = [
            {
                "content": {
                    "title": "Apple news without link",
                }
            }
        ]

        with patch("services.stock_service._fetch_news", return_value=mock_news):
            service = StockService("AAPL")
            news = service.get_news()
            assert news == []

    def test_get_news_handles_missing_thumbnail(self):
        mock_news = [
            {
                "content": {
                    "title": "Apple news",
                    "clickThroughUrl": {"url": "https://example.com/news/1"},
                    "provider": {"displayName": "Reuters"},
                    "pubDate": "2024-01-15T09:00:00Z",
                }
            }
        ]

        with patch("services.stock_service._fetch_news", return_value=mock_news):
            service = StockService("AAPL")
            news = service.get_news()
            assert len(news) == 1
            assert news[0].thumbnail == ""

    def test_get_news_limits_to_five_items(self):
        mock_news = [
            {
                "content": {
                    "title": f"News {i}",
                    "clickThroughUrl": {"url": f"https://example.com/news/{i}"},
                    "provider": {"displayName": "Reuters"},
                    "pubDate": "2024-01-15T09:00:00Z",
                }
            }
            for i in range(10)
        ]

        with patch("services.stock_service._fetch_news", return_value=mock_news):
            service = StockService("AAPL")
            news = service.get_news()
            assert len(news) == 5
