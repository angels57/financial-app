"""User interface components for the dashboard."""

from ui.sidebar import render_sidebar
from ui.tabs import (
    BaseTab,
    FinancialsTab,
    NewsTab,
    PricesTab,
    SummaryTab,
    TechnicalTab,
)

__all__ = [
    "BaseTab",
    "FinancialsTab",
    "NewsTab",
    "PricesTab",
    "SummaryTab",
    "TechnicalTab",
    "render_sidebar",
]
