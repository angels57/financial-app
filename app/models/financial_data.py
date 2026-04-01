"""Modelos de dominio para datos financieros."""

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


class NewsItem(BaseModel):
    """Noticia de una acción."""

    title: str
    link: str
    publisher: str = "Fuente desconocida"
