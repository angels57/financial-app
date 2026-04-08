"""User interface components for the dashboard."""

from ui.sidebar import render_sidebar
from ui.tabs import (
    BaseTab,
    NewsTab,
    OverviewTab,
    PricesTab,
    TechnicalTab,
)

__all__ = [
    "BaseTab",
    "NewsTab",
    "OverviewTab",
    "PricesTab",
    "TechnicalTab",
    "render_sidebar",
]
