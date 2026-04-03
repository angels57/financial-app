"""Domain models for technical analysis."""

from pydantic import BaseModel, Field


class TechnicalIndicatorData(BaseModel):
    """Datos crudos de un indicador técnico para una fecha."""

    indicator: str
    ticker: str
    date: str
    value: float


class SMAResult(BaseModel):
    """Resultado de SMA (Simple Moving Average)."""

    ticker: str
    time_period: int
    interval: str
    data: dict[str, float] = Field(default_factory=dict)

    def to_series(self) -> tuple[list[str], list[float]]:
        dates = sorted(self.data.keys(), reverse=True)
        return dates, [self.data[d] for d in dates]


class RSIResult(BaseModel):
    """Resultado de RSI (Relative Strength Index)."""

    ticker: str
    time_period: int
    interval: str
    data: dict[str, float] = Field(default_factory=dict)

    def to_series(self) -> tuple[list[str], list[float]]:
        dates = sorted(self.data.keys(), reverse=True)
        return dates, [self.data[d] for d in dates]

    def current_value(self) -> float | None:
        if not self.data:
            return None
        sorted_dates = sorted(self.data.keys(), reverse=True)
        return self.data.get(sorted_dates[0])

    def signal(self) -> str:
        val = self.current_value()
        if val is None:
            return "Sin datos"
        if val > 70:
            return "Sobrecompra"
        if val < 30:
            return "Sobreventa"
        return "Neutral"


class TechnicalSignal(BaseModel):
    """Señal de trading interpretada."""

    indicator: str
    signal: str
    value: float
    interpretation: str
    is_strong: bool = False
