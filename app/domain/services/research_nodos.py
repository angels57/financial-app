from typing import TypedDict
from langgraph.graph import StateGraph, END, START


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
    return {}


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
