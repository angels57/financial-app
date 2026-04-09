from __future__ import annotations

from collections.abc import Iterator
import logging
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.domain.services import get_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un analista financiero experto.
  Analiza el ticker dado y genera un reporte estructurado con exactamente estos 10 puntos:
  1. Summary,
  2. What The Company Does,
  3. Market & Competition,
  4. Growth Performance,
  5. Margins & Profitability,
  6. Free Cash Flow,
  7. Management,
  8. Long-Term View,
  9. Valuation,
  10. Should You Buy It.
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

    logger.info(f"Generando reporte para ticker: {ticker}")

    llm = get_llm(provider, model)
    search_tool = DuckDuckGoSearchRun()

    # 1. Crear el agente ReAct
    #    Esto crea un grafo que maneja automáticamente:
    #    LLM → "quiero buscar X" → ejecuta DuckDuckGo → resultado → LLM → respuesta
    agent = create_react_agent(model=llm, tools=[search_tool], prompt=SYSTEM_PROMPT)

    input_messages = {
        "messages": [
            HumanMessage(content=RESEARCH_PROMPT.format(ticker=ticker, context=context))
        ]
    }
    # 3. Streaming token por token
    #  stream_mode="messages" te da cada token individual
    for chunk, metadata in agent.stream(input_messages, stream_mode="messages"):
        # metadata["langgraph_node"] te dice QUIÉN generó el chunk:
        #   - "agent" → es texto del LLM (lo que quieres mostrar)
        #   - "tools" → es el resultado de una herramienta (no lo muestras)
        if (
            hasattr(chunk, "content")
            and chunk.content
            and metadata["langgraph_node"] == "agent"  # type: ignore
        ):
            yield str(chunk.content)
