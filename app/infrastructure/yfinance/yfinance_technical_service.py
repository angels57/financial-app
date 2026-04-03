"""Cálculo de indicadores técnicos desde yfinance localmente."""

import pandas as pd
import yfinance as yf


class YfinanceTechnicalService:
    """Calcula SMA y RSI desde price history de yfinance sin usar API externa."""

    @staticmethod
    def get_sma(ticker: str, period: str, time_period: int) -> dict[str, float] | None:
        """Calcula Simple Moving Average.

        Args:
            ticker: Símbolo (ej. "AAPL")
            period: Período yfinance (ej. "1y", "6mo", "2y")
            time_period: Período de la media móvil (50, 100, 200)

        Returns:
            Dict {fecha_str: valor_sma} o None si hay error
        """
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if hist.empty or "Close" not in hist.columns:
                return None
            sma = hist["Close"].rolling(window=time_period).mean()
            result: dict[str, float] = {}
            for dt, val in sma.dropna().items():
                date_str = pd.Timestamp(dt).strftime("%Y-%m-%d")
                result[date_str] = round(float(val), 2)
            return result if result else None
        except Exception:
            return None

    @staticmethod
    def get_rsi(
        ticker: str, period: str, time_period: int = 14
    ) -> dict[str, float] | None:
        """Calcula Relative Strength Index (RSI).

        Args:
            ticker: Símbolo
            period: Período yfinance
            time_period: Período RSI (default 14)

        Returns:
            Dict {fecha_str: valor_rsi} o None si hay error
        """
        try:
            hist = yf.Ticker(ticker).history(period=period)
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
        except Exception:
            return None

    def get_multiple_sma(
        self, ticker: str, period: str, periods: list[int]
    ) -> dict[int, dict[str, float] | None]:
        """Calcula múltiples SMAs de una sola vez (más eficiente).

        Args:
            ticker: Símbolo
            period: Período yfinance
            periods: Lista de períodos [50, 100, 200]

        Returns:
            Dict {periodo: {fecha: valor_sma}}
        """
        results: dict[int, dict[str, float] | None] = {}
        try:
            hist = yf.Ticker(ticker).history(period=period)
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
        except Exception:
            for p in periods:
                results[p] = None
            return results
