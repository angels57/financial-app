"""Tab implementations for the dashboard."""

from ui.tabs.base import BaseTab
from ui.tabs.financials import FinancialsTab
from ui.tabs.news import NewsTab
from ui.tabs.prices import PricesTab
from ui.tabs.summary import SummaryTab
from ui.tabs.technical import TechnicalTab

__all__ = [
    "BaseTab",
    "FinancialsTab",
    "NewsTab",
    "PricesTab",
    "SummaryTab",
    "TechnicalTab",
]
