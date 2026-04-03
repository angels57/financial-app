"""Chart components for rendering Plotly charts in Streamlit."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render_price_history_chart(
    hist,
    currency: str,
    period: str,
) -> None:
    """Render price history with volume as a subplot."""
    if hist.empty:
        st.warning("No hay datos históricos para este periodo.")
        return

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25],
    )

    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["Close"],
            mode="lines",
            name="Precio",
            line={"color": "#1f77b4", "width": 1.5},
            fill="tozeroy",
            fillcolor="rgba(31,119,180,0.1)",
            hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f} " + currency + "<extra></extra>",
        ),
        row=1,
        col=1,
    )

    if "Volume" in hist.columns:
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist["Volume"],
                name="Volumen",
                marker_color="rgba(31,119,180,0.3)",
                hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        xaxis2={
            "rangeselector": {
                "buttons": [
                    {"count": 1, "label": "1M", "step": "month"},
                    {"count": 3, "label": "3M", "step": "month"},
                    {"count": 6, "label": "6M", "step": "month"},
                    {
                        "count": 1,
                        "label": "YTD",
                        "step": "year",
                        "stepmode": "todate",
                    },
                    {"count": 1, "label": "1Y", "step": "year"},
                    {"label": "Todo", "step": "all"},
                ]
            },
            "rangeslider": {"visible": True},
        },
        yaxis_title=f"Precio ({currency})",
        yaxis2_title="Volumen",
        hovermode="x unified",
        height=600,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        showlegend=False,
    )

    st.plotly_chart(fig, width="stretch")


def render_52_week_range(
    price: float,
    low: float | None,
    high: float | None,
    currency: str,
) -> None:
    """Render a 52-week range bar with current price marker."""
    if not low or not high or high == low:
        st.caption("Rango 52 semanas no disponible")
        return

    pct = ((price - low) / (high - low)) * 100
    pct = max(0.0, min(100.0, pct))

    bar_color = "#2ca02c" if pct < 70 else "#ff7f0e" if pct < 90 else "#d62728"

    st.caption("Rango 52 Semanas")
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:8px; font-size:0.85em;">
            <span>{currency} {low:,.2f}</span>
            <div style="flex:1; position:relative; height:8px;
                        background:#e0e0e0; border-radius:4px;">
                <div style="width:{pct:.1f}%; height:100%;
                            background:{bar_color}; border-radius:4px;"></div>
                <div style="position:absolute; top:-3px; left:calc({pct:.1f}% - 7px);
                            width:14px; height:14px; background:{bar_color};
                            border:2px solid white; border-radius:50%;
                            box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>
            </div>
            <span>{currency} {high:,.2f}</span>
        </div>
        <div style="text-align:center; font-size:0.8em; margin-top:4px; color:#666;">
            {currency} {price:,.2f} — {pct:.0f}% del rango
        </div>
        """,
        unsafe_allow_html=True,
    )
