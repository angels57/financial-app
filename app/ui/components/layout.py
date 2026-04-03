"""Layout helper components for Streamlit pages."""

from __future__ import annotations


def section_divider() -> None:
    """Render a horizontal rule as a section separator."""
    import streamlit as st

    st.markdown("---")


def metric_row(
    *metrics: tuple[str, str],
) -> None:
    """Render a row of metric components.

    Args:
        *metrics: Variable number of (label, value) tuples.
    """
    import streamlit as st

    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
