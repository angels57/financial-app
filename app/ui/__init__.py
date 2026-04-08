"""User interface components for the dashboard."""

from app.ui.sidebar import render_sidebar
from app.ui.tabs import (
    BaseTab,
    NewsTab,
    OverviewTab,
    PricesTab,
    TechnicalTab,
    ResearchTab,
)

__all__ = [
    "BaseTab",
    "NewsTab",
    "OverviewTab",
    "PricesTab",
    "TechnicalTab",
    "ResearchTab",
    "render_sidebar",
]
