from __future__ import annotations

from collections.abc import Iterator

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, SystemMessage

from app.domain.services import get_llm

SYSTEM_PROMPT = """Eres un analista financiero experto.
  Analiza el ticker dado y genera un reporte estructurado con exactamente estos 10 puntos:
  1. Summary, 2. What The Company Does, 3. Market & Competition,
  4. Growth Performance, 5. Margins & Profitability, 6. Free Cash Flow,
  7. Management, 8. Long-Term View, 9. Valuation, 10. Should You Buy It.
  Usa datos concretos, sé objetivo y cita fuentes cuando puedas."""

RESEARCH_PROMPT = """Genera un deep research report completo para: {ticker}

  Contexto financiero disponible:
  {context}

  Estructura el reporte con los 10 puntos obligatorios en Markdown.
  Busca información adicional actualizada en fuentes confiables sobre reportes financieros."""


def generate_report(
    ticker: str,
    context: str,
    provider: str | None = None,
    model: str | None = None,
) -> Iterator[str]:
    """Genera el reporte con streaming. Yields chunks de texto."""

    llm = get_llm()
    # Añadir herramienta de búsqueda si el modelo soporta tool calling
    try:
        search_tool = DuckDuckGoSearchRun()
        llm_with_tools = llm.bind_tools([search_tool])
    except NotImplementedError:
        llm_with_tools = llm

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=RESEARCH_PROMPT.format(ticker=ticker, context=context)),
    ]

    for chunk in llm_with_tools.stream(messages):
        if chunk.content:
            yield str(chunk.content)
