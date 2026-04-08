"""Chart components for rendering Plotly charts in Streamlit."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.ui.theme import (
    COLOR_GROWTH_NEGATIVE,
    COLOR_GROWTH_POSITIVE,
    COLOR_HLINE_MID,
    COLOR_NEUTRAL,
    COLOR_PRICE_LINE,
    COLOR_RSI_COMBINED,
    COLOR_RSI_LINE,
    COLOR_SMA_100,
    RSI_LABEL_OVERBOUGHT,
    RSI_LABEL_OVERSOLD,
)


def render_price_history_chart(
    hist: pd.DataFrame,
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
            line={"color": COLOR_PRICE_LINE, "width": 1.5},
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


def render_price_eps_chart(
    hist: pd.DataFrame,
    eps_series: pd.Series | None,
    currency: str,
    frequency: str = "quarterly",
    benchmark: pd.DataFrame | None = None,
    benchmark_label: str = "S&P 500",
) -> None:
    """Render a combo chart: EPS bars (background) + price line (foreground).

    Inspired by AlphaSpread's overview chart. The EPS bars sit on a hidden
    secondary axis so the price line dominates visually. Optionally overlays
    a normalized benchmark line (e.g. S&P 500) for comparison.
    """
    if hist.empty:
        st.warning("No hay datos históricos para este periodo.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # -- EPS bars (background) on hidden left axis ----------------------
    if eps_series is not None and not eps_series.empty:
        eps_dates = pd.to_datetime(eps_series.index)
        # bar width in milliseconds; quarterly ≈ 60d, annual ≈ 250d
        bar_width_ms = (
            60 * 24 * 3600 * 1000
            if frequency == "quarterly"
            else 250 * 24 * 3600 * 1000
        )
        fig.add_trace(
            go.Bar(
                x=eps_dates,
                y=eps_series.values,
                name="EPS",
                marker_color="rgba(120,140,180,0.22)",
                marker_line_width=0,
                width=bar_width_ms,
                text=[f"{v:.2f}" for v in eps_series.values],
                textposition="outside",
                textfont={"size": 11, "color": "#5f6c7b"},
                hovertemplate="%{x|%b %Y}<br>EPS: %{y:.2f}<extra></extra>",
            ),
            secondary_y=False,
        )
        # Generous range so bars sit at the bottom and leave room for labels
        max_eps = float(max(eps_series.values))
        fig.update_yaxes(
            range=[0, max_eps * 1.5],
            showgrid=False,
            showticklabels=False,
            secondary_y=False,
        )

    # -- Price line (foreground) on visible right axis ------------------
    fig.add_trace(
        go.Scatter(
            x=hist.index,
            y=hist["Close"],
            mode="lines",
            name="Precio",
            line={"color": COLOR_PRICE_LINE, "width": 2},
            fill="tozeroy",
            fillcolor="rgba(31,119,180,0.08)",
            hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f} " + currency + "<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_yaxes(
        title_text=f"Precio ({currency})",
        showgrid=True,
        gridcolor="rgba(200,200,200,0.25)",
        secondary_y=True,
    )

    # -- Optional benchmark line (normalized to start of price) ---------
    if benchmark is not None and not benchmark.empty and not hist.empty:
        b_close = benchmark["Close"]
        b_start = float(b_close.iloc[0])
        h_start = float(hist["Close"].iloc[0])
        if b_start != 0:
            normalized = b_close / b_start * h_start
            fig.add_trace(
                go.Scatter(
                    x=benchmark.index,
                    y=normalized,
                    mode="lines",
                    name=benchmark_label,
                    line={"color": "#888888", "width": 1.4, "dash": "dot"},
                    hovertemplate="%{x|%d %b %Y}<br>"
                    + benchmark_label
                    + " (norm): %{y:,.2f}<extra></extra>",
                ),
                secondary_y=True,
            )

    fig.update_xaxes(
        showgrid=False,
        rangeslider={"visible": False},
    )
    fig.update_layout(
        hovermode="x unified",
        height=500,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        showlegend=benchmark is not None,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.15,
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

    bar_color = (
        COLOR_GROWTH_POSITIVE
        if pct < 70
        else COLOR_NEUTRAL
        if pct < 90
        else COLOR_GROWTH_NEGATIVE
    )

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


# -- Technical chart builder ---------------------------------------------


class _TechnicalChartBuilder:
    """Builder para gráficos técnicos — extrae código común de price, SMA y RSI."""

    _RANGESELECTOR_BUTTONS = [
        {"count": 1, "label": "1M", "step": "month"},
        {"count": 3, "label": "3M", "step": "month"},
        {"count": 6, "label": "6M", "step": "month"},
        {"count": 1, "label": "YTD", "step": "year", "stepmode": "todate"},
        {"count": 1, "label": "1Y", "step": "year"},
        {"label": "Todo", "step": "all"},
    ]

    _PRICE_HOVER = "date_price"

    def __init__(
        self,
        hist: pd.DataFrame,
        currency: str,
        interval: str,
    ) -> None:
        self._hist = hist
        self._currency = currency

    def _price_hover(self) -> str:
        return "%{x|%d %b %Y}<br>%{y:,.2f} " + self._currency + "<extra></extra>"

    def _add_price_trace(
        self,
        fig: go.Figure,
        row: int,
        col: int,
        fillcolor: str = "rgba(31,119,180,0.1)",
    ) -> None:
        fig.add_trace(
            go.Scatter(
                x=self._hist.index,
                y=self._hist["Close"],
                mode="lines",
                name="Precio",
                line={"color": COLOR_PRICE_LINE, "width": 1.5},
                fill="tozeroy",
                fillcolor=fillcolor,
                hovertemplate=self._price_hover(),
            ),
            row=row,
            col=col,
        )

    def _add_volume_trace(
        self,
        fig: go.Figure,
        row: int,
        col: int,
    ) -> None:
        if "Volume" not in self._hist.columns:
            return
        fig.add_trace(
            go.Bar(
                x=self._hist.index,
                y=self._hist["Volume"],
                name="Volumen",
                marker_color="rgba(31,119,180,0.3)",
                hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>",
            ),
            row=row,
            col=col,
        )

    def _apply_rangeselector_and_layout(
        self,
        fig: go.Figure,
        xaxis_key: str,
        yaxis_title: str,
        height: int = 600,
        showlegend: bool = True,
        yaxis2_title: str | None = None,
        yaxis3_title: str | None = None,
        legend: dict | None = None,
    ) -> None:
        layout_updates: dict = {
            xaxis_key: {
                "rangeselector": {"buttons": self._RANGESELECTOR_BUTTONS},
                "rangeslider": {"visible": True},
            },
            "yaxis_title": yaxis_title,
            "hovermode": "x unified",
            "height": height,
            "margin": {"l": 0, "r": 0, "t": 10, "b": 0},
            "showlegend": showlegend,
        }
        if yaxis2_title:
            layout_updates["yaxis2_title"] = yaxis2_title
        if legend:
            layout_updates["legend"] = legend
        # layout_updates built dynamically with str keys; plotly accepts them at runtime
        fig.update_layout(**layout_updates)  # type: ignore[arg-type]
        if yaxis3_title:
            fig.update_layout(yaxis3_title=yaxis3_title)

    # -- SMA-only chart -----------------------------------------------------

    def build_sma_chart(
        self,
        sma_data: dict[int, dict[str, float] | None],
        sma_colors: dict[int, str],
        sma_widths: dict[int, float],
        row_heights: list[float] = [0.75, 0.25],
    ) -> go.Figure:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
        )

        self._add_price_trace(fig, row=1, col=1)
        self._add_sma_traces(fig, sma_data, sma_colors, sma_widths, row=1)
        self._add_volume_trace(fig, row=2, col=1)

        self._apply_rangeselector_and_layout(
            fig,
            xaxis_key="xaxis2",
            yaxis_title=f"Precio ({self._currency})",
            yaxis2_title="Volumen",
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        return fig

    def _add_sma_traces(
        self,
        fig: go.Figure,
        sma_data: dict[int, dict[str, float] | None],
        sma_colors: dict[int, str],
        sma_widths: dict[int, float],
        row: int,
    ) -> None:
        for period, data in sma_data.items():
            if data is None:
                continue
            sorted_dates = sorted(data.keys())
            values = [data[d] for d in sorted_dates]
            dates_pd = pd.to_datetime(sorted_dates)

            fig.add_trace(
                go.Scatter(
                    x=dates_pd,
                    y=values,
                    mode="lines",
                    name=f"SMA {period}",
                    line={
                        "color": sma_colors.get(period, COLOR_SMA_100),
                        "width": sma_widths.get(period, 1.5),
                    },
                    hovertemplate="%{x|%d %b %Y}<br>SMA "
                    + str(period)
                    + ": %{y:,.2f}<extra></extra>",
                ),
                row=row,
                col=1,
            )

    # -- RSI-only chart -----------------------------------------------------

    def build_rsi_chart(
        self,
        rsi_data: dict[str, float],
        time_period: int,
        row_heights: list[float] = [0.4, 0.6],
    ) -> go.Figure:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
        )

        rsi_dates = sorted(rsi_data.keys())
        rsi_values = [rsi_data[d] for d in rsi_dates]
        rsi_dates_pd = pd.to_datetime(rsi_dates)

        self._add_price_trace(fig, row=1, col=1, fillcolor="rgba(31,119,180,0.1)")

        fig.add_trace(
            go.Scatter(
                x=rsi_dates_pd,
                y=rsi_values,
                mode="lines",
                name=f"RSI {time_period}",
                line={"color": COLOR_RSI_LINE, "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(127,127,127,0.2)",
                hovertemplate="%{x|%d %b %Y}<br>RSI: %{y:.2f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        self._add_rsi_hlines(fig, row=2)
        self._apply_rangeselector_and_layout(
            fig,
            xaxis_key="xaxis2",
            yaxis_title=f"Precio ({self._currency})",
            yaxis2_title=f"RSI {time_period}",
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        fig.update_yaxes(range=[0, 100], row=2, col=1)
        return fig

    def _add_rsi_hlines(self, fig: go.Figure, row: int) -> None:
        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color=COLOR_GROWTH_NEGATIVE,
            row=row,
            col=1,
            annotation_text=RSI_LABEL_OVERBOUGHT,
            annotation_position="bottom right",
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color=COLOR_GROWTH_POSITIVE,
            row=row,
            col=1,
            annotation_text=RSI_LABEL_OVERSOLD,
            annotation_position="top right",
        )
        fig.add_hline(y=50, line_dash="dot", line_color=COLOR_HLINE_MID, row=row, col=1)

    # -- Combined SMA + RSI chart -------------------------------------------

    def build_combined_chart(
        self,
        sma_data: dict[int, dict[str, float] | None],
        rsi_data: dict[str, float],
        time_period: int,
        sma_colors: dict[int, str],
        sma_widths: dict[int, float],
        row_heights: list[float] = [0.45, 0.25, 0.30],
    ) -> go.Figure:
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
        )

        self._add_price_trace(fig, row=1, col=1)
        self._add_sma_traces(fig, sma_data, sma_colors, sma_widths, row=1)
        self._add_volume_trace(fig, row=2, col=1)

        rsi_dates = sorted(rsi_data.keys())
        rsi_values = [rsi_data[d] for d in rsi_dates]
        rsi_dates_pd = pd.to_datetime(rsi_dates)

        fig.add_trace(
            go.Scatter(
                x=rsi_dates_pd,
                y=rsi_values,
                mode="lines",
                name=f"RSI {time_period}",
                line={"color": COLOR_RSI_COMBINED, "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(155,89,182,0.2)",
                hovertemplate="%{x|%d %b %Y}<br>RSI: %{y:.2f}<extra></extra>",
            ),
            row=3,
            col=1,
        )

        self._add_rsi_hlines(fig, row=3)
        self._apply_rangeselector_and_layout(
            fig,
            xaxis_key="xaxis3",
            yaxis_title=f"Precio ({self._currency})",
            yaxis2_title="Volumen",
            yaxis3_title=f"RSI {time_period}",
            height=700,
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        fig.update_yaxes(range=[0, 100], row=3, col=1)
        return fig
