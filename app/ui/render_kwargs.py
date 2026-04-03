"""TypedDict definitions for UI render kwargs — ensures type-safe contract between main and tabs."""

from __future__ import annotations

import logging
from typing import TypedDict

from models import FinancialMetrics, StockInfo
from services.protocols import StockDataFetcherProtocol


class RenderKwargs(TypedDict, total=False):
    """Keyword arguments passed to tab.render() — enables static analysis of UI contracts."""

    stock_service: StockDataFetcherProtocol
    info: StockInfo
    period: str
    ticker: str
    metrics: FinancialMetrics
    logger: logging.Logger
