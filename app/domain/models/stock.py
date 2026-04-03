"""Domain models for stock data."""

from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    """Información general de una acción."""

    ticker: str
    short_name: str
    price: float
    currency: str
    market_cap: float | None = None
    pe_ratio: float | None = None
    volume: int = 0
    week_52_low: float | None = None
    week_52_high: float | None = None
    sector: str = ""
    industry: str = ""
    country: str = ""
    employees: int | None = None
    website: str = ""
    description: str = ""
    beta: float | None = None
    dividend_yield: float | None = None
    eps: float | None = None
    target_price: float | None = None
    recommendation: str = ""
    shares_outstanding: float | None = None
    forward_pe: float | None = None
    price_to_sales: float | None = None
    price_to_fcf: float | None = None
    total_revenue: float | None = None
    free_cash_flow: float | None = None
    net_income: float | None = None


class ChartSeries(BaseModel):
    """Serie de datos para gráficos."""

    x: list[str]
    y: list[float]


class FinancialMetrics(BaseModel):
    """Métricas financieras calculadas."""

    years: list[str] = Field(default_factory=list)
    revenue_billions: list[float] = Field(default_factory=list)
    net_income_billions: list[float] = Field(default_factory=list)
    sales_growth: list[float] = Field(default_factory=list)
    net_margin: list[float] = Field(default_factory=list)
    roe: list[float] = Field(default_factory=list)
    fcf_billions: list[float] = Field(default_factory=list)
    debt_billions: list[float] = Field(default_factory=list)
    debt_equity: list[float] = Field(default_factory=list)
    pe_ratio: float | None = None

    def to_summary_chart_data(self) -> dict[str, ChartSeries]:
        """Convierte las métricas a datos para el gráfico de resumen multi-línea."""
        data: dict[str, ChartSeries] = {}

        if self.sales_growth:
            data["Crecimiento Ventas"] = ChartSeries(x=self.years, y=self.sales_growth)
        if self.net_margin:
            data["Margen Neto (%)"] = ChartSeries(x=self.years, y=self.net_margin)
        if self.roe:
            data["ROE (%)"] = ChartSeries(x=self.years, y=self.roe)
        if self.fcf_billions:
            data["FCF"] = ChartSeries(x=self.years, y=self.fcf_billions)
        if self.debt_equity:
            data["Deuda/Equity (%)"] = ChartSeries(x=self.years, y=self.debt_equity)
        if self.pe_ratio and self.years:
            data["PER"] = ChartSeries(x=[self.years[-1]], y=[self.pe_ratio])

        return data

    def yoy_deltas(self) -> dict[str, tuple[float | None, float | None, bool]]:
        """Retorna el último valor y delta YoY para cada KPI.

        Los datos vienen ordenados del más reciente al más antiguo,
        así que [0] es el año más reciente y [1] es el anterior.
        """
        import math

        def _safe(values: list[float], key: str, is_pct: bool) -> None:
            if len(values) >= 2:
                curr, prev = values[0], values[1]
                if math.isfinite(curr) and math.isfinite(prev):
                    deltas[key] = (curr, curr - prev, is_pct)
                    return
            if values and math.isfinite(values[0]):
                deltas[key] = (values[0], None, is_pct)

        deltas: dict[str, tuple[float | None, float | None, bool]] = {}
        _safe(self.revenue_billions, "Revenue", False)
        _safe(self.net_margin, "Net Margin", True)
        _safe(self.fcf_billions, "FCF", False)
        _safe(self.debt_equity, "Debt/Equity", True)
        return deltas
