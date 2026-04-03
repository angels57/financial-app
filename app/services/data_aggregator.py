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
from services.yfinance_technical_service import YfinanceTechnicalService

logger = logging.getLogger(__name__)


class DataAggregator:
    """Facade: DB cache -> yfinance -> (Alpha Vantage in the future)."""

    def __init__(self, ticker: str, cache_repo: CacheRepository | None = None):
        self._ticker_symbol = ticker
        self._yf = StockService(ticker)
        self._cache = cache_repo
        self._av_service = self._init_alpha_vantage()
        self._yf_tech = YfinanceTechnicalService()
        self._tech_source = "yfinance"

    def set_technical_source(self, source: str) -> None:
        """Establece la fuente de indicadores técnicos.

        Args:
            source: "yfinance" o "alphavantage"
        """
        self._tech_source = source

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
                logger.info("[%s] Info obtenida desde cache", self._ticker_symbol)
                return cached

        logger.info("[%s] Obteniendo info desde yfinance...", self._ticker_symbol)
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
                logger.info(
                    "[%s] Precios (%s) obtenidos desde cache",
                    self._ticker_symbol,
                    period,
                )
                return cached

        logger.info(
            "[%s] Obteniendo precios (%s) desde yfinance...",
            self._ticker_symbol,
            period,
        )
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
                logger.info("[%s] Noticias obtenidas desde cache", self._ticker_symbol)
                return cached

        logger.info("[%s] Obteniendo noticias desde yfinance...", self._ticker_symbol)
        news = self._yf.get_news()

        if self._cache and news:
            self._cache.upsert_news(self._ticker_symbol, news, source="yfinance")
        return news

    # -- Technical Indicators (routing by source) --------------------------------

    _SMA_TTL = 14400
    _RSI_TTL = 3600

    _INTERVAL_TO_PERIOD = {
        "daily": "1y",
        "weekly": "5y",
    }

    def get_sma(
        self,
        time_period: int = 20,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None:
        if self._tech_source == "yfinance":
            return self._get_sma_yfinance(time_period, interval, force_refresh)
        else:
            return self._get_sma_alphavantage(time_period, interval, force_refresh)

    def get_multiple_sma(
        self,
        periods: list[int] | None = None,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[int, dict[str, float] | None]:
        """Obtiene múltiples SMAs simultáneamente."""
        if periods is None:
            periods = [50, 100, 200]
        if self._tech_source == "yfinance":
            return self._get_multiple_sma_yfinance(periods, interval, force_refresh)
        else:
            return self._get_multiple_sma_alphavantage(periods, interval, force_refresh)

    def get_rsi(
        self,
        time_period: int = 14,
        interval: str = "daily",
        force_refresh: bool = False,
    ) -> dict[str, float] | None:
        if self._tech_source == "yfinance":
            return self._get_rsi_yfinance(time_period, interval, force_refresh)
        else:
            return self._get_rsi_alphavantage(time_period, interval, force_refresh)

    # -- yfinance implementation -------------------------------------------------

    def _get_sma_yfinance(
        self, time_period: int, interval: str, force_refresh: bool
    ) -> dict[str, float] | None:
        period = self._INTERVAL_TO_PERIOD.get(interval, "1y")
        indicator_key = "SMA_YF"

        if self._cache and not force_refresh:
            cached = self._cache.get_technical_indicator(
                self._ticker_symbol, indicator_key, interval, time_period, self._SMA_TTL
            )
            if cached is not None:
                logger.info(
                    "[%s] SMA (%s, %d) desde cache yfinance",
                    self._ticker_symbol,
                    interval,
                    time_period,
                )
                return cached

        logger.info(
            "[%s] Calculando SMA (%s, %s) desde yfinance...",
            self._ticker_symbol,
            interval,
            time_period,
        )
        result = self._yf_tech.get_sma(self._ticker_symbol, period, time_period)

        if result and self._cache:
            self._cache.upsert_technical_indicator(
                self._ticker_symbol,
                indicator_key,
                interval,
                time_period,
                result,
                source="yfinance",
            )
        return result

    def _get_rsi_yfinance(
        self, time_period: int, interval: str, force_refresh: bool
    ) -> dict[str, float] | None:
        period = self._INTERVAL_TO_PERIOD.get(interval, "1y")
        indicator_key = "RSI_YF"

        if self._cache and not force_refresh:
            cached = self._cache.get_technical_indicator(
                self._ticker_symbol, indicator_key, interval, time_period, self._RSI_TTL
            )
            if cached is not None:
                logger.info(
                    "[%s] RSI (%s, %d) desde cache yfinance",
                    self._ticker_symbol,
                    interval,
                    time_period,
                )
                return cached

        logger.info(
            "[%s] Calculando RSI (%s, %s) desde yfinance...",
            self._ticker_symbol,
            interval,
            time_period,
        )
        result = self._yf_tech.get_rsi(self._ticker_symbol, period, time_period)

        if result and self._cache:
            self._cache.upsert_technical_indicator(
                self._ticker_symbol,
                indicator_key,
                interval,
                time_period,
                result,
                source="yfinance",
            )
        return result

    def _get_multiple_sma_yfinance(
        self, periods: list[int], interval: str, force_refresh: bool
    ) -> dict[int, dict[str, float] | None]:
        period = self._INTERVAL_TO_PERIOD.get(interval, "1y")
        indicator_key = "SMA_YF"

        results: dict[int, dict[str, float] | None] = {}
        cached_results: dict[int, dict[str, float] | None] = {}

        if self._cache and not force_refresh:
            for p in periods:
                cached = self._cache.get_technical_indicator(
                    self._ticker_symbol, indicator_key, interval, p, self._SMA_TTL
                )
                if cached is not None:
                    cached_results[p] = cached
                    logger.info(
                        "[%s] SMA %d (%s) desde cache yfinance",
                        self._ticker_symbol,
                        p,
                        interval,
                    )
            if len(cached_results) == len(periods):
                return cached_results

        logger.info(
            "[%s] Calculando múltiples SMAs (%s) desde yfinance...",
            self._ticker_symbol,
            interval,
        )
        raw_results = self._yf_tech.get_multiple_sma(
            self._ticker_symbol, period, periods
        )

        for p in periods:
            if p in cached_results:
                results[p] = cached_results[p]
            else:
                data = raw_results.get(p) if raw_results else None
                results[p] = data
                if data and self._cache:
                    self._cache.upsert_technical_indicator(
                        self._ticker_symbol,
                        indicator_key,
                        interval,
                        p,
                        data,
                        source="yfinance",
                    )

        return results

    def _get_multiple_sma_alphavantage(
        self, periods: list[int], interval: str, force_refresh: bool
    ) -> dict[int, dict[str, float] | None]:
        if self._av_service is None:
            logger.warning("[%s] Alpha Vantage no disponible", self._ticker_symbol)
            return {p: None for p in periods}

        indicator_key = "SMA_AV"
        results: dict[int, dict[str, float] | None] = {}

        for p in periods:
            if self._cache and not force_refresh:
                cached = self._cache.get_technical_indicator(
                    self._ticker_symbol, indicator_key, interval, p, self._SMA_TTL
                )
                if cached is not None:
                    logger.info(
                        "[%s] SMA %d (%s) desde cache alphavantage",
                        self._ticker_symbol,
                        p,
                        interval,
                    )
                    results[p] = cached
                    continue

            logger.info(
                "[%s] Obteniendo SMA %d (%s) desde Alpha Vantage...",
                self._ticker_symbol,
                p,
                interval,
            )
            result = self._av_service.get_sma(self._ticker_symbol, interval, p)
            data = result.data if result else None
            results[p] = data

            if data and self._cache:
                self._cache.upsert_technical_indicator(
                    self._ticker_symbol,
                    indicator_key,
                    interval,
                    p,
                    data,
                    source="alphavantage",
                )

        return results

    # -- Alpha Vantage implementation -------------------------------------------

    def _get_sma_alphavantage(
        self, time_period: int, interval: str, force_refresh: bool
    ) -> dict[str, float] | None:
        if self._av_service is None:
            logger.warning(
                "[%s] Alpha Vantage no disponible para SMA", self._ticker_symbol
            )
            return None

        indicator_key = "SMA_AV"

        if self._cache and not force_refresh:
            cached = self._cache.get_technical_indicator(
                self._ticker_symbol, indicator_key, interval, time_period, self._SMA_TTL
            )
            if cached is not None:
                logger.info(
                    "[%s] SMA (%s, %d) desde cache alphavantage",
                    self._ticker_symbol,
                    interval,
                    time_period,
                )
                return cached

        logger.info(
            "[%s] Obteniendo SMA (%s, %d) desde Alpha Vantage...",
            self._ticker_symbol,
            interval,
            time_period,
        )
        result = self._av_service.get_sma(self._ticker_symbol, interval, time_period)
        if result is None:
            return None

        if self._cache:
            self._cache.upsert_technical_indicator(
                self._ticker_symbol,
                indicator_key,
                interval,
                time_period,
                result.data,
                source="alphavantage",
            )
        return result.data

    def _get_rsi_alphavantage(
        self, time_period: int, interval: str, force_refresh: bool
    ) -> dict[str, float] | None:
        if self._av_service is None:
            logger.warning(
                "[%s] Alpha Vantage no disponible para RSI", self._ticker_symbol
            )
            return None

        indicator_key = "RSI_AV"

        if self._cache and not force_refresh:
            cached = self._cache.get_technical_indicator(
                self._ticker_symbol, indicator_key, interval, time_period, self._RSI_TTL
            )
            if cached is not None:
                logger.info(
                    "[%s] RSI (%s, %d) desde cache alphavantage",
                    self._ticker_symbol,
                    interval,
                    time_period,
                )
                return cached

        logger.info(
            "[%s] Obteniendo RSI (%s, %d) desde Alpha Vantage...",
            self._ticker_symbol,
            interval,
            time_period,
        )
        result = self._av_service.get_rsi(self._ticker_symbol, interval, time_period)
        if result is None:
            return None

        if self._cache:
            self._cache.upsert_technical_indicator(
                self._ticker_symbol,
                indicator_key,
                interval,
                time_period,
                result.data,
                source="alphavantage",
            )
        return result.data

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
                logger.info(
                    "[%s] %s obtenido desde cache", self._ticker_symbol, statement
                )
                return cached

        logger.info(
            "[%s] Obteniendo %s desde yfinance...", self._ticker_symbol, statement
        )
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
            logger.info(
                "[%s] Complementando info desde Alpha Vantage...", self._ticker_symbol
            )
            av_info = self._av_service.get_info(self._ticker_symbol)
        except Exception:
            logger.warning(
                "[%s] Error al obtener info desde Alpha Vantage, usando solo yfinance",
                self._ticker_symbol,
            )
            return yf_info
        if av_info is None:
            logger.warning(
                "[%s] Alpha Vantage no devolvió datos de info, usando solo yfinance",
                self._ticker_symbol,
            )
            return yf_info

        yf_dict = yf_info.model_dump()
        av_dict = av_info.model_dump()
        filled = []
        for key, val in yf_dict.items():
            if val is None or val == "":
                av_val = av_dict.get(key)
                if av_val is not None and av_val != "":
                    yf_dict[key] = av_val
                    filled.append(key)
        if filled:
            logger.info(
                "[%s] Alpha Vantage completó campos faltantes: %s",
                self._ticker_symbol,
                ", ".join(filled),
            )
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
            logger.info(
                "[%s] Complementando %s desde Alpha Vantage...",
                self._ticker_symbol,
                statement,
            )
            result = getattr(self._av_service, method_name)(self._ticker_symbol)
            if result is None:
                logger.warning(
                    "[%s] Alpha Vantage no devolvió datos para %s",
                    self._ticker_symbol,
                    statement,
                )
            return result
        except Exception:
            logger.warning(
                "[%s] Error al obtener %s desde Alpha Vantage, usando solo yfinance",
                self._ticker_symbol,
                statement,
            )
            return None

    @staticmethod
    def _merge_dataframe(
        yf_df: pd.DataFrame | None, av_df: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if yf_df is not None and av_df is not None:
            return yf_df if len(yf_df.index) >= len(av_df.index) else av_df
        return yf_df if yf_df is not None else av_df
