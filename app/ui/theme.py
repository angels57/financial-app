"""Shared UI constants: colors, labels, and financial terminology.

All hardcoded strings and color codes used across tabs and components
should be defined here to avoid duplication and enable consistent styling.
"""

# -- Price and chart colors ---------------------------------------------

COLOR_PRICE_LINE = "#1f77b4"
COLOR_GROWTH_POSITIVE = "#2ca02c"
COLOR_GROWTH_NEGATIVE = "#d62728"
COLOR_NEUTRAL = "#ff7f0e"

# -- SMA period colors -------------------------------------------------

COLOR_SMA_50 = "#ff7f0e"
COLOR_SMA_100 = "#7f7f7f"
COLOR_SMA_200 = "#2ca02c"

SMA_COLORS = {50: COLOR_SMA_50, 100: COLOR_SMA_100, 200: COLOR_SMA_200}
SMA_WIDTHS = {50: 2.0, 100: 1.5, 200: 1.0}

# -- RSI colors and thresholds ----------------------------------------

COLOR_RSI_LINE = "#7f7f7f"
COLOR_RSI_COMBINED = "#9b59b6"
COLOR_HLINE_MID = "#999999"

RSI_OVERBOUGHT_THRESHOLD = 70
RSI_OVERSOLD_THRESHOLD = 30

# -- Financial metric colors -------------------------------------------

METRIC_COLORS = {
    "Total Revenue": "#1f77b4",
    "Net Income": "#2ca02c",
    "Free Cash Flow": "#ff7f0e",
    "Total Debt": "#d62728",
}

# -- Spanish financial labels -----------------------------------------

LABEL_CRECIMIENTO = "Crecimiento (%)"
LABEL_MARGEN = "Margen (%)"

# -- RSI zone labels --------------------------------------------------

RSI_ZONE_OVERBOUGHT = "Sobrecompra"
RSI_ZONE_OVERSOLD = "Sobreventa"
RSI_ZONE_NEUTRAL = "Neutral"
RSI_LABEL_OVERBOUGHT = "Sobrecompra (70)"
RSI_LABEL_OVERSOLD = "Sobreventa (30)"
