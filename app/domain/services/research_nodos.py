from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from app.infrastructure.yfinance.client import YFinanceClient
from app.domain.services import FinancialCalculator


class ReportState(TypedDict):
    ticker: str
    financial_data: str  # datos de yfinance
    search_results: str  # resultados de busqueda
    section_company: str  # secciones 2,3
    section_financial: str  # secciones 4,5,6
    section_macro: str  # secciones 8,9
    section_mgmt: str  # secciones 1,7,10
    final_report: str  # reporte final


def collect_data(state: ReportState) -> dict:
    """Recopila datos financieros de yfinance."""
    ticker = state["ticker"]

    # 1. Crear el cliente de yfinance (sin caché, es un proceso puntual)
    client = YFinanceClient(ticker)

    # 2. Obtener datos crudos
    info = client.get_info()
    finanials = client.get_financials()
    balance = client.get_balance_sheet()
    cashflow = client.get_cashflow()
    dividends = client.get_dividends()

    # 3. Calcular métricas derivadas con tu calculadora existente
    calculator = FinancialCalculator()
    metrics = calculator.compute(
        financials=finanials,
        balance=balance,
        cashflow=cashflow,
        pe_ratio=info.pe_ratio,
    )
    # 4. Construir un contexto rico en texto para los nodos siguientes

    financial_data = f"""
    === DATOS FINANCIEROS: {info.short_name} ({ticker}) ===

    --- Información General ---
    Nombre: {info.short_name}
    Sector: {info.sector} | Industria: {info.industry}
    País: {info.country}
    Empleados: {info.employees}
    Descripción: {info.description}
    Web: {info.website}

    --- Precio y Mercado ---
    Precio Actual: {info.currency} {info.price:,.2f}
    Market Cap: {info.market_cap:,.0f}
    Volumen: {info.volume:,}
    52-Week Low: {info.week_52_low}
    52-Week High: {info.week_52_high}
    Beta: {info.beta}

    --- Valoración ---
    P/E Ratio: {info.pe_ratio}
    Forward P/E: {info.forward_pe}
    Price/Sales: {info.price_to_sales}
    Price/FCF: {info.price_to_fcf}
    EPS: {info.eps}
    Target Price (analistas): {info.target_price}
    Recomendación: {info.recommendation}

    --- Rentabilidad (series históricas) ---
    Años: {metrics.years}
    Revenue (B): {metrics.revenue_billions}
    Net Income (B): {metrics.net_income_billions}
    Sales Growth (%): {metrics.sales_growth}
    Net Margin (%): {metrics.net_margin}
    ROE (%): {metrics.roe}

    --- Cash Flow ---
    FCF (B): {metrics.fcf_billions}

    --- Deuda ---
    Deuda Total (B): {metrics.debt_billions}
    Debt/Equity (%): {metrics.debt_equity}

    --- Dividendos ---
    Dividend Yield: {info.dividend_yield}
    Historial: {dividends.to_string() if dividends is not None else "N/A"}

    --- EPS Histórico ---
    EPS por año: {metrics.eps}
        """

    return {"financial_data": financial_data}


def research(state: ReportState) -> dict:
    """Ejecuta múltiples búsquedas paralelas."""
    return {}


def analyze_company(state: ReportState) -> dict:
    """Genera secciones 2 y 3 con un prompt especializado."""
    return {}


def analyze_financials(state: ReportState) -> dict:
    """Genera secciones 4, 5, 6."""
    return {}


def analyze_macro(state: ReportState) -> dict:
    """Genera secciones 8, 9."""
    return {}


def write_summary_and_recommendation(state: ReportState) -> dict:
    """Genera secciones 1, 7, 10 (necesita las demás)."""
    return {}


def synthesize(state: ReportState) -> dict:
    """Une todo en un reporte final coherente."""
    return {}


# Construir el grafo
graph = StateGraph(ReportState)

graph.add_node("collect_data", collect_data)
graph.add_node("research", research)
graph.add_node("company", analyze_company)
graph.add_node("financials", analyze_financials)
graph.add_node("macro", analyze_macro)
graph.add_node("mgmt", write_summary_and_recommendation)
graph.add_node("synthesize", synthesize)

# definir el flujo
graph.add_edge(START, "collect_data")
graph.add_edge("collect_data", "research")

# nodos paralelos
graph.add_edge("research", "company")
graph.add_edge("research", "financials")
graph.add_edge("research", "macro")

# Estos esperan a que los 3 anteriores terminen
graph.add_edge("company", "mgmt")
graph.add_edge("financials", "mgmt")
graph.add_edge("macro", "mgmt")

graph.add_edge("mgmt", "synthesize")
graph.add_edge("synthesize", END)

workflow = graph.compile()
