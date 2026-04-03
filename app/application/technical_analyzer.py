"""Technical analyzer — orchestrates technical indicator computation."""

from __future__ import annotations

from infrastructure.yfinance.yfinance_technical_service import YfinanceTechnicalService


class TechnicalAnalyzer:
    """Orchestrates technical indicator fetching and computation."""

    def __init__(self, yf_tech_service: YfinanceTechnicalService):
        self._tech_service = yf_tech_service

    def get_sma(
        self,
        ticker: str,
        period: str,
        time_period: int,
    ) -> dict[str, float] | None:
        """Fetch SMA indicator."""
        return self._tech_service.get_sma(ticker, period, time_period)  # type: ignore[no-any-return]

    def get_multiple_sma(
        self,
        ticker: str,
        periods: list[int],
        interval: str,
    ) -> dict[int, dict[str, float] | None]:
        """Fetch multiple SMA indicators."""
        return self._tech_service.get_multiple_sma(ticker, periods, interval)  # type: ignore[no-any-return]

    def get_rsi(
        self,
        ticker: str,
        period: str,
        time_period: int = 14,
    ) -> dict[str, float] | None:
        """Fetch RSI indicator."""
        return self._tech_service.get_rsi(ticker, period, time_period)  # type: ignore[no-any-return]
