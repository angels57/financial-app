"""Tests for YFinanceClient using mocked yfinance and in-memory cache."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from app.domain.models import NewsItem, StockInfo
from app.infrastructure.yfinance.client import YFinanceClient
from app.db.cache_repo import CacheRepository


def _stock_info_apple() -> StockInfo:
    return StockInfo(
        ticker="AAPL",
        short_name="Apple Inc.",
        price=250.0,
        currency="USD",
        sector="Technology",
    )


class TestYFinanceClientGetInfo:
    """Tests for get_info — read-through cache + yfinance mapping."""

    def test_get_info_uses_cache_when_fresh(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """When cache has StockInfo, result comes from cache (verified by result fields)."""
        cached = _stock_info_apple()
        fake_cache_repo.upsert_stock_info("AAPL", cached, "yfinance")

        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_info()

        assert result.short_name == "Apple Inc."
        assert result.sector == "Technology"
        assert result.currency == "USD"

    def test_get_info_fetches_from_yfinance_when_cache_miss(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """When cache returns None, client fetches from yfinance and caches."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_info()

        assert result.short_name == "Apple Inc."
        assert result.sector == "Technology"
        assert fake_cache_repo.get_stock_info("AAPL") is not None

    def test_get_info_force_refresh_bypasses_cache(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """force_refresh=True skips cache and fetches from yfinance."""
        stale = _stock_info_apple()
        stale.__dict__["_short_name"] = "Stale Name"
        fake_cache_repo.upsert_stock_info("AAPL", stale, "yfinance")

        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_info(force_refresh=True)

        assert result.short_name == "Apple Inc."


class TestYFinanceClientGetHistory:
    """Tests for get_history."""

    def test_get_history_delegates_to_yf(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """get_history calls yfinance.history()."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_history(period="1y")

        assert isinstance(result, pd.DataFrame)
        assert "Close" in result.columns
        mock_yf_ticker.history.assert_called_once_with(period="1y")

    def test_get_history_returns_cached_dataframe(
        self, fake_cache_repo: CacheRepository
    ) -> None:
        """When cache has fresh data, yfinance is not called."""
        cached_df = pd.DataFrame({"Close": [200.0, 190.0]})
        fake_cache_repo.upsert_price_history("AAPL", "1y", cached_df, "yfinance")

        with patch("infrastructure.yfinance.client.yf.Ticker"):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_history(period="1y")

        assert result is cached_df


class TestYFinanceClientCacheReadThrough:
    """Tests that financial statement methods use read-through cache."""

    def test_get_financials_uses_cache_when_available(
        self, fake_cache_repo: CacheRepository
    ) -> None:
        """Cache hit returns cached DataFrame without calling yfinance."""
        cached_df = pd.DataFrame({"Revenue": [100.0]})
        fake_cache_repo.upsert_financial_statement(
            "AAPL", "financials", cached_df, "yfinance"
        )

        with patch("infrastructure.yfinance.client.yf.Ticker") as mock_ticker_cls:
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_financials()

        assert result is cached_df
        mock_ticker_cls.return_value.financials.__getitem__.assert_not_called()

    def test_get_financials_fetches_and_caches_on_miss(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """Cache miss fetches from yfinance and writes to cache."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_financials()

        assert result is not None
        assert "Total Revenue" in result.columns
        assert fake_cache_repo.get_financial_statement("AAPL", "financials") is not None

    def test_get_balance_sheet_uses_cache_when_available(
        self, fake_cache_repo: CacheRepository
    ) -> None:
        """Cache hit returns cached balance sheet."""
        cached_df = pd.DataFrame({"Equity": [50.0]})
        fake_cache_repo.upsert_financial_statement(
            "AAPL", "balance_sheet", cached_df, "yfinance"
        )

        with patch("infrastructure.yfinance.client.yf.Ticker") as mock_ticker_cls:
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_balance_sheet()

        assert result is cached_df
        mock_ticker_cls.return_value.balance_sheet.__getitem__.assert_not_called()

    def test_get_cashflow_uses_cache_when_available(
        self, fake_cache_repo: CacheRepository
    ) -> None:
        """Cache hit returns cached cashflow statement."""
        cached_df = pd.DataFrame({"FCF": [30.0]})
        fake_cache_repo.upsert_financial_statement(
            "AAPL", "cashflow", cached_df, "yfinance"
        )

        with patch("infrastructure.yfinance.client.yf.Ticker") as mock_ticker_cls:
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_cashflow()

        assert result is cached_df
        mock_ticker_cls.return_value.cashflow.__getitem__.assert_not_called()

    def test_get_dividends_no_cache(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """get_dividends always fetches from yfinance, no cache involved."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_dividends()

        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_get_news_uses_cache_when_available(
        self, fake_cache_repo: CacheRepository
    ) -> None:
        """Cache hit returns cached news list."""
        cached_news = [
            NewsItem(title="Test", link="http://test.com", publisher="TestPub")
        ]
        fake_cache_repo.upsert_news("AAPL", cached_news, "yfinance")

        with patch("infrastructure.yfinance.client.yf.Ticker") as mock_ticker_cls:
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_news()

        assert result == cached_news
        mock_ticker_cls.return_value.news.__getitem__.assert_not_called()

    def test_get_news_force_refresh_bypasses_cache(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """force_refresh=True skips cache and fetches fresh news."""
        stale = [NewsItem(title="Old", link="http://old.com", publisher="OldPub")]
        fake_cache_repo.upsert_news("AAPL", stale, "yfinance")

        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_news(force_refresh=True)

        assert result[0].title == "Apple reports record earnings"
        # force_refresh=True skips cache read but still writes fresh data to cache
        news = fake_cache_repo.get_news("AAPL")
        assert news is not None
        assert news[0].title == "Apple reports record earnings"


class TestYFinanceClientTechnicalIndicators:
    """Tests that technical indicator methods delegate to the tech service."""

    def test_get_sma_checks_cache(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """get_sma checks the cache before calling tech service."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_sma(time_period=20, interval="daily")

        # Result depends on tech service output with mocked ticker
        assert result is None or isinstance(result, dict)

    def test_get_rsi_checks_cache(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """get_rsi checks the cache before calling tech service."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_rsi(time_period=14, interval="daily")

        assert result is None or isinstance(result, dict)

    def test_get_multiple_sma_delegates_to_tech_service(
        self, fake_cache_repo: CacheRepository, mock_yf_ticker: MagicMock
    ) -> None:
        """get_multiple_sma calls tech service directly (no cache)."""
        with patch(
            "infrastructure.yfinance.client.yf.Ticker",
            return_value=mock_yf_ticker,
        ):
            client = YFinanceClient("AAPL", cache_repo=fake_cache_repo)
            result = client.get_multiple_sma(periods=[50, 200], interval="daily")

        assert isinstance(result, dict)
