from typing import Optional

import plotly.graph_objects as go


def calculate_yoy_growth(values: list[float]) -> list[float]:
    """Calculate year-over-year growth rates for a list of values.

    Returns a list of the same length where the first element is 0.0
    and subsequent elements are the percentage change from the previous value.
    """
    yoy = []
    for i in range(len(values)):
        if i == 0:
            yoy.append(0.0)
        else:
            if values[i - 1] > 0:
                growth = ((values[i] - values[i - 1]) / values[i - 1]) * 100
                yoy.append(growth)
            else:
                yoy.append(0.0)
    return yoy


def calculate_cagr(values: list[float]) -> float | None:
    """Calculate Compound Annual Growth Rate from a list of values.

    Expects values ordered chronologically (oldest first).
    Returns the CAGR as a percentage, or None if it cannot be computed.
    """
    if len(values) < 2:
        return None
    start, end = values[0], values[-1]
    if start <= 0 or end <= 0:
        return None
    n = len(values) - 1
    return ((end / start) ** (1 / n) - 1) * 100


def draw_plotly_grouped_bar_chart(
    series: dict[str, list[float]],
    labels: list[str],
    title: str,
    ylabel: str,
    colors: dict[str, str] | None = None,
) -> go.Figure:
    """Draw a grouped bar chart with multiple series."""
    import math

    fig = go.Figure()
    default_colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd"]

    for i, (name, values) in enumerate(series.items()):
        color = (colors or {}).get(name, default_colors[i % len(default_colors)])
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                name=name,
                marker_color=color,
                text=[f"${v:.2f}B" if math.isfinite(v) else "" for v in values],
                textposition="outside",
            )
        )

    fig.update_layout(
        title={"text": title, "font": {"size": 14}, "y": 0.95},
        xaxis_title="Año",
        yaxis_title=ylabel,
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        height=400,
        margin={"l": 0, "r": 0, "t": 80, "b": 0},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0.5,
            "xanchor": "center",
        },
    )
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.1)")

    return fig


def calculate_52_week_delta(
    current_price: float, reference_price: Optional[float]
) -> Optional[float]:
    if reference_price is None:
        return None
    return ((current_price - reference_price) / reference_price) * 100


def draw_plotly_bar_chart(
    values: list,
    labels: list,
    title: str,
    ylabel: str,
    color: str = "#1f77b4",
    is_percent: bool = False,
    signed: bool = False,
) -> go.Figure:
    if signed:
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in values]
    else:
        colors = [color] * len(values)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"{v:+.1f}{'%' if is_percent else 'B'}" for v in values],
            textposition="outside",
        )
    )

    fig.update_layout(
        title={"text": title, "font": {"size": 14}},
        xaxis_title="Year",
        yaxis_title=ylabel,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=350,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
    )

    if signed:
        fig.add_hline(y=0, line_width=0.5, line_color="black")

    fig.update_yaxes(gridcolor="rgba(0,0,0,0.1)")

    return fig


def draw_plotly_multi_line_chart(
    data: dict,
    title: str,
    ylabel: str,
    is_percent: bool = False,
) -> go.Figure:
    fig = go.Figure()

    for label, values in data.items():
        fig.add_trace(
            go.Scatter(
                x=values["x"],
                y=values["y"],
                mode="lines+markers",
                name=label,
                line={"width": 2},
            )
        )

    fig.update_layout(
        title={"text": title, "font": {"size": 14}, "y": 0.95},
        xaxis_title="Year",
        yaxis_title=ylabel,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        height=400,
        margin={"l": 0, "r": 0, "t": 80, "b": 0},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0.5,
            "xanchor": "center",
        },
    )

    if is_percent:
        fig.update_yaxes(tickformat=".1f%")

    fig.update_xaxes(gridcolor="rgba(0,0,0,0.1)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.1)")

    return fig


def draw_plotly_dual_axis_chart(
    bar_values: list,
    line_values: list,
    labels: list,
    title: str,
    bar_label: str,
    line_label: str,
    bar_color: str = "#1f77b4",
    line_color: str = "#2ca02c",
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=labels,
            y=bar_values,
            name=bar_label,
            marker_color=bar_color,
            text=[f"${v:.2f}" for v in bar_values],
            textposition="outside",
            yaxis="y",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=labels,
            y=line_values,
            name=line_label,
            mode="lines+markers",
            line=dict(color=line_color, width=2),
            yaxis="y2",
            text=[f"{v:+.1f}%" for v in line_values],
            textposition="top center",
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        title={"text": title, "font": {"size": 14}, "y": 0.95},
        xaxis=dict(
            title="Año",
            gridcolor="rgba(0,0,0,0.1)",
        ),
        yaxis=dict(
            title=dict(text=bar_label, font=dict(color=bar_color)),
            tickfont=dict(color=bar_color),
            gridcolor="rgba(0,0,0,0.1)",
            side="left",
        ),
        yaxis2=dict(
            title=dict(text=line_label, font=dict(color=line_color)),
            tickfont=dict(color=line_color),
            overlaying="y",
            side="right",
            showticklabels=True,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        height=400,
        margin={"l": 50, "r": 50, "t": 80, "b": 0},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0.5,
            "xanchor": "center",
        },
        showlegend=True,
    )

    return fig
