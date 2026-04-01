def format_large_number(value: float | None, currency: str = "") -> str:
    if value is None:
        return "N/A"

    if value >= 1_000_000_000_000:
        return (
            f"{currency} {value / 1_000_000_000_000:.2f}T"
            if currency
            else f"{value / 1_000_000_000_000:.2f}T"
        )
    elif value >= 1_000_000_000:
        return (
            f"{currency} {value / 1_000_000_000:.2f}B"
            if currency
            else f"{value / 1_000_000_000:.2f}B"
        )
    elif value >= 1_000_000:
        return (
            f"{currency} {value / 1_000_000:.2f}M"
            if currency
            else f"{value / 1_000_000:.2f}M"
        )
    elif value >= 1_000:
        return (
            f"{currency} {value / 1_000:.2f}K" if currency else f"{value / 1_000:.2f}K"
        )
    else:
        return f"{currency} {value:,.2f}" if currency else f"{value:,.2f}"
