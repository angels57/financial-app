"""DataAggregator — facade that combines caching + multiple data sources.

Drop-in replacement for StockService. Exposes the same method signatures
so all UI tabs work without changes.
"""

import logging

import pandas as pd

from config import settings
from db.cache_repo import CacheRepository
from models import NewsItem, StockInfo
from services.stock_service import StockService

logger = logging.getLogger(__name__)


class DataAggregator:
    """Facade: DB cache -> yfinance -> (Alpha Vantage in the future)."""

    def __init__(self, ticker: str, cache_repo: CacheRepository | None = None):
        self._ticker_symbol = ticker
        self._yf = StockService(ticker)
        self._cache = cache_repo
        self._av_service = self._init_alpha_vantage()

    @property
    def ticker(self) -> str:
        return self._ticker_symbol

    @staticmethod
    def _init_alpha_vantage():
        """Initialize Alpha Vantage service if API key is configured."""
        if not settings.alpha_vantage_api_key:
            logger.warning(
                "ALPHA_VANTAGE_API_KEY no configurada — Alpha Vantage no se usará como fuente secundaria. "
                "Configura la variable de entorno ALPHA_VANTAGE_API_KEY en tu archivo .env para habilitar datos complementarios."
            )
            return None
        try:
            from services.alpha_vantage_service import AlphaVantageService

            return AlphaVantageService(settings.alpha_vantage_api_key)
        except Exception:
            logger.exception("Failed to initialize Alpha Vantage service")
            return None

    # -- Public API (same signatures as StockService) -------------------------

    def get_info(self, force_refresh: bool = False) -> StockInfo:
        if self._cache and not force_refresh:
            cached = self._cache.get_stock_info(self._ticker_symbol)
            if cached is not None:
                return cached

        yf_info = self._yf.get_info()
        merged = self._merge_info(yf_info)

        if self._cache:
            self._cache.upsert_consulted_company(
                self._ticker_symbol, merged.short_name, merged.sector
            )
            self._cache.upsert_stock_info(self._ticker_symbol, merged, source="merged")

        return merged

    def get_history(self, period: str) -> pd.DataFrame:
        ttl = settings.price_cache_ttl_seconds
        if self._cache:
            cached = self._cache.get_price_history(self._ticker_symbol, period, ttl)
            if cached is not None:
                return cached

        df = self._yf.get_history(period)

        if self._cache and not df.empty:
            self._cache.upsert_price_history(
                self._ticker_symbol, period, df, source="yfinance"
            )
        return df

    def get_financials(self, force_refresh: bool = False) -> pd.DataFrame | None:
        return self._get_statement("financials", self._yf.get_financials, force_refresh)

    def get_balance_sheet(self, force_refresh: bool = False) -> pd.DataFrame | None:
        return self._get_statement(
            "balance_sheet", self._yf.get_balance_sheet, force_refresh
        )

    def get_cashflow(self, force_refresh: bool = False) -> pd.DataFrame | None:
        return self._get_statement("cashflow", self._yf.get_cashflow, force_refresh)

    def get_dividends(self, force_refresh: bool = False) -> pd.DataFrame | None:
        return self._get_statement("dividends", self._yf.get_dividends, force_refresh)

    def get_news(self, force_refresh: bool = False) -> list[NewsItem]:
        if self._cache and not force_refresh:
            cached = self._cache.get_news(self._ticker_symbol)
            if cached is not None:
                return cached

        news = self._yf.get_news()

        if self._cache and news:
            self._cache.upsert_news(self._ticker_symbol, news, source="yfinance")
        return news

    # -- Private helpers ------------------------------------------------------

    def _get_statement(
        self,
        statement: str,
        yf_fetcher: callable,
        force_refresh: bool = False,
    ) -> pd.DataFrame | None:
        if self._cache and not force_refresh:
            cached = self._cache.get_financial_statement(self._ticker_symbol, statement)
            if cached is not None:
                return cached

        yf_df = yf_fetcher()
        av_df = self._fetch_av_statement(statement)
        result = self._merge_dataframe(yf_df, av_df)

        if self._cache and result is not None:
            source = "merged" if av_df is not None and yf_df is not None else "yfinance"
            self._cache.upsert_financial_statement(
                self._ticker_symbol, statement, result, source=source
            )
        return result

    def _merge_info(self, yf_info: StockInfo) -> StockInfo:
        if self._av_service is None:
            return yf_info
        try:
            av_info = self._av_service.get_info(self._ticker_symbol)
        except Exception:
            logger.warning("Alpha Vantage get_info failed, using yfinance only")
            return yf_info
        if av_info is None:
            return yf_info

        yf_dict = yf_info.model_dump()
        av_dict = av_info.model_dump()
        for key, val in yf_dict.items():
            if val is None or val == "":
                av_val = av_dict.get(key)
                if av_val is not None and av_val != "":
                    yf_dict[key] = av_val
        return StockInfo(**yf_dict)

    def _fetch_av_statement(self, statement: str) -> pd.DataFrame | None:
        if self._av_service is None:
            return None
        method_map = {
            "financials": "get_financials",
            "balance_sheet": "get_balance_sheet",
            "cashflow": "get_cashflow",
        }
        method_name = method_map.get(statement)
        if method_name is None:
            return None
        try:
            return getattr(self._av_service, method_name)(self._ticker_symbol)
        except Exception:
            logger.warning("Alpha Vantage %s failed", statement)
            return None

    @staticmethod
    def _merge_dataframe(
        yf_df: pd.DataFrame | None, av_df: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if yf_df is not None and av_df is not None:
            return yf_df if len(yf_df.index) >= len(av_df.index) else av_df
        return yf_df if yf_df is not None else av_df
