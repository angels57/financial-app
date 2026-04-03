"""Badge components for displaying metric differences and indicators."""

from __future__ import annotations

import streamlit as st


def render_diff_badge(diff: float, label: str = "upside") -> None:
    """Renderiza una etiqueta de diferencia con colores y fondo."""
    if diff > 0:
        color = "#1e7e34"
        bg = "#e6f4ea"
    elif diff < 0:
        color = "#c0392b"
        bg = "#fce8e6"
    else:
        color = "#5f6368"
        bg = "#f1f3f4"
    st.markdown(
        f'<span style="color:{color}; background:{bg}; font-size:0.78em; '
        f'padding:2px 8px; border-radius:4px; font-weight:500;">'
        f"{label}: {diff:+.1f}%</span>",
        unsafe_allow_html=True,
    )
