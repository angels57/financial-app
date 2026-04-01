from typing import Optional

import matplotlib.pyplot as plt


def calculate_52_week_delta(
    current_price: float, reference_price: Optional[float]
) -> Optional[float]:
    if reference_price is None:
        return None
    return ((current_price - reference_price) / reference_price) * 100


def draw_bar_chart(
    values: list,
    labels: list,
    title: str,
    ylabel: str,
    color: str = "#1f77b4",
    is_percent: bool = False,
    signed: bool = False,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    if signed:
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in values]
    else:
        colors = color if isinstance(color, str) else color
    ax.bar(labels, values, color=colors)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3, axis="y")
    if signed:
        ax.axhline(y=0, color="black", linewidth=0.5)
    for i, v in enumerate(values):
        offset = 1 if not signed or v >= 0 else -1.5
        if is_percent:
            ax.text(i, v + offset, f"{v:.1f}%", ha="center", fontsize=9)
        else:
            prefix = "$" if not is_percent else ""
            suffix = "B" if not is_percent else "%"
            ax.text(i, v + offset, f"{prefix}{v:.1f}{suffix}", ha="center", fontsize=9)
    return fig


def draw_multi_line_chart(
    data: dict,
    title: str,
    ylabel: str,
    is_percent: bool = False,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    for label, values in data.items():
        ax.plot(values["x"], values["y"], marker="o", linewidth=2, label=label)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", framealpha=0.9)
    if is_percent:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    fig.autofmt_xdate()
    return fig
