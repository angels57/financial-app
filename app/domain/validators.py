"""Domain-level validation rules."""

from __future__ import annotations

import re

_TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")


def validate_ticker(ticker: str) -> str | None:
    """Returns None if valid, error message if invalid."""
    if not ticker:
        return "Ticker is required"
    if not _TICKER_PATTERN.match(ticker):
        return "Ticker inválido. Usa entre 1-5 letras (ej: AAPL, TSLA, BRK.B)."
    return None


def require_valid_ticker(ticker: str) -> str:
    """Raises ValueError if invalid, returns ticker otherwise."""
    error = validate_ticker(ticker)
    if error:
        raise ValueError(error)
    return ticker
