from typing import Optional

import plotly.graph_objects as go


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
        title={"text": title, "font": {"size": 14}},
        xaxis_title="Year",
        yaxis_title=ylabel,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        height=400,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
    )

    if is_percent:
        fig.update_yaxes(tickformat=".1f%")

    fig.update_xaxes(gridcolor="rgba(0,0,0,0.1)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.1)")

    return fig
