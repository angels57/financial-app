from typing import Optional


def calculate_52_week_delta(
    current_price: float, reference_price: Optional[float]
) -> Optional[float]:
    if reference_price is None:
        return None
    return ((current_price - reference_price) / reference_price) * 100
