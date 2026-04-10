from typing import TypedDict
import logging
from langgraph.graph import StateGraph, END, START
from app.infrastructure.yfinance.client import YFinanceClient
from app.domain.services.calculator import FinancialCalculator
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import SystemMessage, HumanMessage
from app.domain.services.research_llm import get_llm

logger = logging.getLogger(__name__)


class ReportState(TypedDict):
    ticker: str
    financial_data: str  # datos de yfinance
    search_results: str  # resultados de busqueda
    section_company: str  # secciones 2,3
    section_financial: str  # secciones 4,5,6
    section_macro: str  # secciones 8,9
    section_mgmt: str  # secciones 1,7,10
    final_report: str  # reporte final


def collect_data(state: ReportState) -> dict[str, str]:
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


def research(state: ReportState) -> dict[str, str]:
    """Ejecuta múltiples búsquedas web especializadas sobre el ticker."""
    ticker = state["ticker"]
    search = DuckDuckGoSearchRun()

    # Definir búsquedas especializadas por tema
    queries = {
        "company_overview": f"{ticker} company overview business model 2025 2026",
        "competition": f"{ticker} competitors market share industry analysis",
        "financials": f"{ticker} earnings revenue growth financial results",
        "management": f"{ticker} CEO management team leadership strategy",
        "valuation": f"{ticker} stock valuation intrinsic value DCF analysis",
        "macro": "stock market outlook 2026 interest rates inflation macro economy",
        "risks": f"{ticker} risks challenges regulatory concerns",
    }
    results_parts: list[str] = []
    for topic, query in queries.items():
        try:
            result = search.invoke(query)
            results_parts.append(
                f"=== BÚSQUEDA: {topic.upper()} ===\n"
                f"Query: {query}\n"
                f"Resultados:\n{result}\n"
            )
        except Exception as e:
            logger.error(f"Error buscando [{topic}]: {e}")
            results_parts.append(
                f"=== BÚSQUEDA: {topic.upper()} ===\nSin resultados disponibles.\n"
            )

    search_results = "\n".join(results_parts)

    return {"search_results": search_results}


def analyze_company(state: ReportState) -> dict[str, str]:
    """Genera secciones 2 (What The Company Does) y 3 (Market & Competition)."""
    llm = get_llm()

    system = SystemMessage(
        content="""Eres un analista de equity research senior
    especializado en análisis cualitativo de empresas. Escribe en español profesional
    con formato Markdown. Incluye tablas comparativas cuando sea relevante.
    Basa tu análisis en datos concretos, nunca inventes información."""
    )

    human = HumanMessage(
        content=f"""
        Con los siguientes datos financieros REALES de la empresa:
        {state["financial_data"]}
        Y esta investigación complementaria de fuentes externas:
        {state["search_results"]}
        Genera EXACTAMENTE estas 2 secciones del reporte de equity research:
        ## 2. What The Company Does
        - Describe el modelo de negocio en profundidad (no solo "qué vende")
        - Explica cómo genera ingresos: productos vs servicios vs suscripciones
        - Integración vertical: ¿controla la cadena de valor? ¿diseña, fabrica, distribuye?
        - Segmentos de negocio principales y su rol estratégico
        - Evolución reciente: ¿hacia dónde está pivotando la empresa?
        - Incluye una tabla con: Segmento | Descripción | Rol Estratégico
        ## 3. Market & Competition
        - Tamaño del mercado (TAM) y posición competitiva de la empresa
        - Principales competidores y sus fortalezas/debilidades relativas
        - Foso económico (Economic Moat): costos de cambio, marca, efecto de red, patentes
        - Amenazas disruptivas o regulatorias al modelo de negocio
        - Incluye una tabla con: Competidor | Sector de Confrontación | Ventaja de la Empresa
        IMPORTANTE:
        - Usa los datos de Sector, Industria y Descripción proporcionados
        - Escribe como un analista de Morningstar o Goldman Sachs
        - Cada sección debe tener 3-4 párrafos con subtítulos + tabla resumen
        """
    )

    response = llm.invoke([system, human])
    return {"section_company": str(response.content)}


def analyze_financials(state: ReportState) -> dict[str, str]:
    """Genera secciones 4 (Growth), 5 (Margins & Profitability) y 6 (FCF)."""
    llm = get_llm()
    system = SystemMessage(
        content="""Eres un analista financiero cuantitativo senior.
    Tu especialidad es el análisis de estados financieros, márgenes de rentabilidad
    y flujos de caja. Escribe en español profesional con formato Markdown.
    Incluye tablas con datos concretos. NUNCA inventes cifras, usa solo los datos
    proporcionados."""
    )

    human = HumanMessage(
        content=f"""
    Datos financieros REALES extraídos de Yahoo Finance:
    {state["financial_data"]}
    Investigación complementaria de fuentes externas:
    {state["search_results"]}
    Genera EXACTAMENTE estas 3 secciones:
    ## 4. Growth Performance
    ### Evolución de los Ingresos y Beneficios
    - Analiza la tendencia de Revenue (B) y Net Income (B) año a año
    - Calcula la CAGR (tasa de crecimiento anual compuesta) con los datos de Sales Growth (%)
    - ¿El crecimiento se está acelerando, desacelerando o estancando?
    ### Motor de Crecimiento
    - Identifica qué segmentos están impulsando el crecimiento
    - ¿Hay señales de saturación en el negocio principal?
    Incluye una tabla:
    | Métrica de Crecimiento | Tasa Histórica | Perspectiva |

    ## 5. Margins & Profitability
    ### Análisis de Márgenes
    - Usa Net Margin (%) para analizar la evolución de la rentabilidad
    - Compara con promedios del sector ({state.get("ticker", "")})
    - ¿Los márgenes están expandiéndose o contrayéndose? ¿Por qué?
    ### Retorno sobre el Capital
    - Analiza ROE (%) y su tendencia
    - Relaciona Debt/Equity (%) con el ROE: ¿el ROE alto es real o apalancado?
    - Calcula eficiencia operativa comparando Revenue vs Net Income
    Incluye una tabla:
    | Métrica de Rentabilidad | Valor | Comparativa Sectorial |
    ## 6. Free Cash Flow
    ### Magnitud y Calidad del FCF
    - Analiza FCF (B) y calcula el margen FCF/Revenue
    - ¿El FCF cubre cómodamente los dividendos? (usa Dividend Yield)
    - ¿Cuánta deuda tiene? (Deuda Total B) ¿El FCF puede cubrirla?
    ### Destino del Capital
    - Con los datos de Dividend Yield y Debt/Equity, infiere la estrategia:
      ¿prioriza recompras, dividendos, reducción de deuda o reinversión?
    Incluye una tabla:
    | Uso del FCF | Estrategia | Beneficio para el Accionista |
    REGLAS:
    - Usa EXCLUSIVAMENTE los números proporcionados en los datos financieros
    - Si un dato es N/A o None, menciona que no está disponible
    - Cada sección: 3-4 párrafos + subtítulos + tabla resumen
    - Tono: analista de Morningstar o Goldman Sachs
    """
    )
    response = llm.invoke([system, human])
    return {"section_financial": str(response.content)}


def analyze_macro(state: ReportState) -> dict[str, str]:
    """Genera secciones 8 (Long-Term View) y 9 (Valuation)."""

    llm = get_llm()

    system = SystemMessage(
        content="""Eres un estratega macro y analista de valoración
    senior. Tu especialidad es conectar el entorno macroeconómico global con la
    valoración intrínseca de empresas. Escribe en español profesional con formato
    Markdown. Incluye tablas comparativas. NUNCA inventes cifras."""
    )

    human = HumanMessage(
        content=f"""
    Datos financieros REALES de la empresa:

    {state["financial_data"]}

    Investigación de fuentes externas (incluye datos macro):

    {state["search_results"]}

    Genera EXACTAMENTE estas 2 secciones:

    ## 8. Long-Term View
    ### La Próxima Frontera
    - ¿En qué nuevas tecnologías o mercados está apostando la empresa?
    - ¿Tiene ventaja competitiva sostenible a 5-10 años?
    - ¿Qué tendencias seculares la benefician o amenazan?

    ### Riesgos Estructurales y Regulatorios
    - Riesgos regulatorios: antimonopolio, privacidad, aranceles
    - Riesgos geopolíticos: dependencia de China, conflictos comerciales
    - Riesgos tecnológicos: disrupciones de IA, cambios de plataforma

    ### Adaptabilidad
    - ¿La empresa ha demostrado capacidad de reinventarse?
    - Diversificación geográfica y de ingresos

    Incluye una tabla:
    | Vector Estratégico | Oportunidad | Riesgo |

    ## 9. Valuation
    ### Valoración Intrínseca
    - Con los datos de P/E Ratio, Forward P/E, Price/Sales y Price/FCF,
      evalúa si la acción está sobrevalorada, infravalorada o a valor justo
    - Compara el P/E actual con el Forward P/E: ¿el mercado espera
      crecimiento o contracción?
    - Si hay Target Price de analistas, compáralo con el precio actual

    ### Análisis de Múltiplos
    - ¿El P/E es alto o bajo para el sector ({state.get("ticker", "")})?
    - ¿El Price/FCF sugiere que el mercado paga una prima excesiva?
    - EPS actual vs histórico: ¿tendencia alcista o bajista?

    ### Contexto de Mercado
    - Usa la información macro de las búsquedas: tasas de interés,
      inflación, sentimiento del mercado
    - ¿Cómo afectan las condiciones macro a la valoración de esta empresa?
    - Beta de la acción: ¿es más o menos volátil que el mercado?

    Incluye una tabla:
    | Método de Valoración | Valor/Métrica | Estado Actual |

    REGLAS:
    - Usa los datos de P/E, Forward P/E, Price/Sales, Price/FCF, Beta,
      Target Price y EPS proporcionados
    - Si un dato es None, menciona que no está disponible
    - Cada sección: 3-4 párrafos + subtítulos + tabla
    - Tono: estratega de JPMorgan o BlackRock
    """
    )

    response = llm.invoke([system, human])
    return {"section_macro": str(response.content)}


def write_summary_and_recommendation(state: ReportState) -> dict[str, str]:
    """Genera secciones 1 (Summary), 7 (Management) y 10 (Should You Buy It)."""

    llm = get_llm()

    system = SystemMessage(
        content="""Eres el director de research de un banco de
    inversión de primer nivel. Tu rol es sintetizar los análisis de tu equipo en
    conclusiones ejecutivas y recomendaciones de inversión. Escribe en español
    profesional con formato Markdown. Sé objetivo, riguroso y directo."""
    )

    human = HumanMessage(
        content=f"""
    Tu equipo de analistas ha producido los siguientes análisis parciales:

    === ANÁLISIS DE EMPRESA Y COMPETENCIA ===
    {state["section_company"]}

    === ANÁLISIS FINANCIERO ===
    {state["section_financial"]}

    === ANÁLISIS MACRO Y VALORACIÓN ===
    {state["section_macro"]}

    Datos financieros de referencia:
    {state["financial_data"]}

    Ahora genera EXACTAMENTE estas 3 secciones que completan el reporte:

    ## 1. Summary
    - Resume en 2-3 párrafos densos las conclusiones principales de TODO el análisis
    - Incluye: calidad del negocio, valoración, perspectiva y recomendación
    - Menciona las cifras más relevantes (precio, P/E, market cap, márgenes)
    - Sintetiza la tesis de inversión en una frase clara
    - Incluye una tabla ejecutiva:
    | Indicador Clave | Valor Actual | Perspectiva |

    ## 7. Management
    - Evalúa la calidad de la gerencia basándote en los resultados financieros
    - Un equipo que logra márgenes altos y crecimiento constante = buena gestión
    - ¿La asignación de capital es eficiente? (mira FCF, dividendos, deuda)
    - ¿El ROE y márgenes sugieren disciplina operativa?
    - Credibilidad: ¿los resultados son consistentes año a año?
    - NO inventes nombres de ejecutivos si no los tienes en los datos

    ## 10. Should You Buy It
    ### Argumentos para la Prudencia
    - Sintetiza los riesgos principales identificados en las secciones anteriores
    - ¿La valoración actual ofrece margen de seguridad?

    ### Recomendación Estratégica
    - Emite una recomendación clara: COMPRAR / MANTENER / ESPERAR
    - Para inversores actuales: ¿deben mantener o vender?
    - Para nuevos inversores: ¿es buen momento para entrar?
    - Define un rango de precio de entrada ideal si recomiendas esperar
    - Justifica tu recomendación con datos concretos del análisis

    Cierra con un párrafo de conclusión y un disclaimer legal.

    REGLAS:
    - Esta sección resume TODO, así que referencia hallazgos de las otras secciones
    - Sé directo con la recomendación, no seas ambiguo
    - Incluye cifras concretas del análisis financiero y de valoración
    - Tono: director de research de Goldman Sachs o Morgan Stanley
    """
    )

    response = llm.invoke([system, human])
    return {"section_mgmt": str(response.content)}


def synthesize(state: ReportState) -> dict[str, str]:
    """Usa el LLM para unificar estilo y reordenar las secciones."""

    llm = get_llm()

    system = SystemMessage(
        content="""Eres un editor senior de reportes financieros.
    Tu trabajo es tomar secciones escritas por diferentes analistas y unificarlas
    en un solo documento coherente, profesional y bien estructurado en Markdown."""
    )

    human = HumanMessage(
        content=f"""
    A continuación tienes las secciones de un reporte de equity research para {state["ticker"]}.
    Fueron escritas por diferentes analistas. Tu tarea es:

    1. REORDENAR las secciones en este orden exacto:
       1. Summary, 2. What The Company Does, 3. Market & Competition,
       4. Growth Performance, 5. Margins & Profitability, 6. Free Cash Flow,
       7. Management, 8. Long-Term View, 9. Valuation, 10. Should You Buy It

    2. UNIFICAR el tono y estilo para que parezca escrito por una sola persona

    3. CORREGIR inconsistencias entre secciones (si una dice "crecimiento alto"
       y otra dice "estancamiento", reconcília con los datos)

    4. Agregar un título principal y un disclaimer al final

    5. NO elimines contenido ni tablas, solo reorganiza y pule

    === SECCIONES DEL EQUIPO ===

    {state["section_mgmt"]}

    {state["section_company"]}

    {state["section_financial"]}

    {state["section_macro"]}
    """
    )
    try:
        response = llm.invoke([system, human])
        return {"final_report": str(response.content)}
    except Exception as e:
        logger.error(f"Error al sintetizar: {e}")
        return {"final_report": f"Error al sintetizar: {e}"}


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
