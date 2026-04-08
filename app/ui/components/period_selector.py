"""Period selector pills with per-period % change badges."""

from __future__ import annotations

import pandas as pd
import streamlit as st

# (yfinance period code, display label)
_PERIODS: list[tuple[str, str]] = [
    ("1mo", "1M"),
    ("6mo", "6M"),
    ("1y", "1Y"),
    ("3y", "3Y"),
    ("5y", "5Y"),
    ("10y", "10Y"),
    ("max", "All"),
]

_PERIOD_OFFSETS = {
    "1mo": pd.DateOffset(months=1),
    "6mo": pd.DateOffset(months=6),
    "1y": pd.DateOffset(years=1),
    "3y": pd.DateOffset(years=3),
    "5y": pd.DateOffset(years=5),
    "10y": pd.DateOffset(years=10),
}


def calc_period_pct_change(history: pd.DataFrame, period: str) -> float | None:
    """Calculate price % change over a period using a full history DataFrame."""
    if history.empty or "Close" not in history.columns:
        return None

    closes = history["Close"]
    end = float(closes.iloc[-1])
    last_date = history.index[-1]

    if period == "max":
        start_idx = 0
    else:
        offset = _PERIOD_OFFSETS.get(period)
        if offset is None:
            return None
        target = last_date - offset
        # Strip tz to avoid datetime64[us] vs Timestamp(tz) comparison errors
        idx = history.index
        if hasattr(idx, "tz") and idx.tz is not None:
            idx = idx.tz_localize(None)
        if hasattr(target, "tzinfo") and target.tzinfo is not None:
            target = target.replace(tzinfo=None)
        start_idx = int(idx.searchsorted(target))
        if start_idx >= len(history):
            return None

    start = float(closes.iloc[start_idx])
    if start == 0:
        return None
    return ((end - start) / start) * 100


def slice_history_to_period(history: pd.DataFrame, period: str) -> pd.DataFrame:
    """Slice a full history DataFrame down to the requested period."""
    if history.empty or period == "max":
        return history
    offset = _PERIOD_OFFSETS.get(period)
    if offset is None:
        return history
    last_date = history.index[-1]
    target = last_date - offset
    # Strip tz to avoid datetime64[us] vs Timestamp(tz) comparison errors
    idx = history.index
    if hasattr(idx, "tz") and idx.tz is not None:
        idx = idx.tz_localize(None)
    if hasattr(target, "tzinfo") and target.tzinfo is not None:
        target = target.replace(tzinfo=None)
    return history[idx >= target]


def render_period_pills(
    history: pd.DataFrame,
    key: str = "overview_period",
    default: str = "5y",
) -> str:
    """Render period selector pills. Returns the selected period code."""
    if key not in st.session_state:
        st.session_state[key] = default

    cols = st.columns(len(_PERIODS))
    selected = st.session_state[key]

    for col, (period, label) in zip(cols, _PERIODS):
        pct = calc_period_pct_change(history, period)
        is_active = period == selected
        pct_str = f"{pct:+.1f}%" if pct is not None else "—"

        with col:
            if st.button(
                f"{label}  {pct_str}",
                key=f"{key}_btn_{period}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state[key] = period
                st.rerun()

    return str(st.session_state[key])
