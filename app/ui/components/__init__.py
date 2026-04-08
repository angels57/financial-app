"""Reusable UI components for the dashboard."""

from ui.components.badges import render_diff_badge
from ui.components.charts import (
    render_52_week_range,
    render_price_eps_chart,
    render_price_history_chart,
)
from ui.components.layout import metric_row, section_divider
from ui.components.period_selector import (
    calc_period_pct_change,
    render_period_pills,
    slice_history_to_period,
)

__all__ = [
    "calc_period_pct_change",
    "render_diff_badge",
    "render_52_week_range",
    "render_period_pills",
    "render_price_eps_chart",
    "render_price_history_chart",
    "metric_row",
    "section_divider",
    "slice_history_to_period",
]
