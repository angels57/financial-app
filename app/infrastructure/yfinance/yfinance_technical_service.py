"""Cálculo de indicadores técnicos desde yfinance localmente."""

import pandas as pd
import yfinance as yf

_INTERVAL_MAP: dict[str, str] = {
    "daily": "1d",
    "weekly": "1wk",
}

# Enough history to compute the longest SMA (200) with margin.
_LOOKBACK_PERIOD = "2y"


class YfinanceTechnicalService:
    """Calcula SMA y RSI desde price history de yfinance sin usar API externa."""

    @staticmethod
    def get_sma(
        ticker: str,
        interval: str,
        time_period: int,
        hist: pd.DataFrame | None = None,
    ) -> dict[str, float] | None:
        """Calcula Simple Moving Average.

        Args:
            ticker: Símbolo (ej. "AAPL")
            interval: Granularidad de datos (ej. "daily", "weekly", "1d", "1wk")
            time_period: Período de la media móvil (50, 100, 200)
            hist: DataFrame de historial pre-fetched. Si es None, se descarga desde yfinance.

        Returns:
            Dict {fecha_str: valor_sma} o None si hay error
        """
        try:
            yf_interval = _INTERVAL_MAP.get(interval, interval)
            if hist is None:
                hist = yf.Ticker(ticker).history(
                    period=_LOOKBACK_PERIOD, interval=yf_interval
                )
            if hist.empty or "Close" not in hist.columns:
                return None
            sma = hist["Close"].rolling(window=time_period).mean()
            result: dict[str, float] = {}
            for dt, val in sma.dropna().items():
                date_str = pd.Timestamp(dt).strftime("%Y-%m-%d")
                result[date_str] = round(float(val), 2)
            return result if result else None
        except (KeyError, ValueError, TypeError):
            return None

    @staticmethod
    def get_rsi(
        ticker: str,
        interval: str,
        time_period: int = 14,
        hist: pd.DataFrame | None = None,
    ) -> dict[str, float] | None:
        """Calcula Relative Strength Index (RSI).

        Args:
            ticker: Símbolo
            interval: Granularidad de datos (ej. "daily", "weekly", "1d", "1wk")
            time_period: Período RSI (default 14)
            hist: DataFrame de historial pre-fetched. Si es None, se descarga desde yfinance.

        Returns:
            Dict {fecha_str: valor_rsi} o None si hay error
        """
        try:
            yf_interval = _INTERVAL_MAP.get(interval, interval)
            if hist is None:
                hist = yf.Ticker(ticker).history(
                    period=_LOOKBACK_PERIOD, interval=yf_interval
                )
            if hist.empty or "Close" not in hist.columns:
                return None

            delta = hist["Close"].diff()
            gain = delta.where(delta > 0, 0.0)
            loss = (-delta).where(delta < 0, 0.0)

            avg_gain = gain.rolling(window=time_period).mean()
            avg_loss = loss.rolling(window=time_period).mean()

            rs = avg_gain / avg_loss
            rs = rs.replace([float("inf"), -float("inf")], float("nan"))
            rsi = 100 - (100 / (1 + rs))

            result: dict[str, float] = {}
            for dt, val in rsi.dropna().items():
                date_str = pd.Timestamp(dt).strftime("%Y-%m-%d")
                result[date_str] = round(float(val), 2)
            return result if result else None
        except (KeyError, ValueError, TypeError):
            return None

    def get_multiple_sma(
        self,
        ticker: str,
        interval: str,
        periods: list[int],
        hist: pd.DataFrame | None = None,
    ) -> dict[int, dict[str, float] | None]:
        """Calcula múltiples SMAs de una sola vez (más eficiente).

        Args:
            ticker: Símbolo
            interval: Granularidad de datos (ej. "daily", "weekly", "1d", "1wk")
            periods: Lista de períodos [50, 100, 200]
            hist: DataFrame de historial pre-fetched. Si es None, se descarga desde yfinance.

        Returns:
            Dict {periodo: {fecha: valor_sma}}
        """
        results: dict[int, dict[str, float] | None] = {}
        try:
            yf_interval = _INTERVAL_MAP.get(interval, interval)
            if hist is None:
                hist = yf.Ticker(ticker).history(
                    period=_LOOKBACK_PERIOD, interval=yf_interval
                )
            if hist.empty or "Close" not in hist.columns:
                for p in periods:
                    results[p] = None
                return results

            close = hist["Close"]
            for p in periods:
                sma = close.rolling(window=p).mean()
                result: dict[str, float] = {}
                for dt, val in sma.dropna().items():
                    date_str = pd.Timestamp(dt).strftime("%Y-%m-%d")
                    result[date_str] = round(float(val), 2)
                results[p] = result if result else None
            return results
        except (KeyError, ValueError, TypeError):
            for p in periods:
                results[p] = None
            return results
