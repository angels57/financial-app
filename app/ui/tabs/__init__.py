"""Tab implementations for the dashboard."""

from app.ui.tabs.base import BaseTab
from app.ui.tabs.news import NewsTab
from app.ui.tabs.overview import OverviewTab
from app.ui.tabs.prices import PricesTab
from app.ui.tabs.technical import TechnicalTab

__all__ = [
    "BaseTab",
    "NewsTab",
    "OverviewTab",
    "PricesTab",
    "TechnicalTab",
]
