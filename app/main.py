import streamlit as st

from config import settings
from core import get_app_logger, init_monitoring
from db import get_pool, init_db
from db.cache_repo import CacheRepository
from services import DataAggregator, FinancialCalculator
from ui import (
    FinancialsTab,
    NewsTab,
    PricesTab,
    SummaryTab,
    TechnicalTab,
    render_sidebar,
)

logger = get_app_logger("")


def _init_database() -> CacheRepository | None:
    """Initialize DB pool, schema, and return a CacheRepository (or None)."""
    pool = get_pool()
    if pool is None:
        return None
    init_db(pool)
    return CacheRepository(pool)


def main():
    st.set_page_config(
        page_title="Financial Stre", layout="wide", initial_sidebar_state="expanded"
    )
    init_monitoring(dsn=settings.sentry_dsn, environment=settings.environment)

    cache_repo = _init_database()

    ticker, period = render_sidebar(cache_repo=cache_repo)

    if not ticker:
        st.title("Bienvenido a Financial Stre")
        st.info(
            "Por favor, introduce un ticker en el panel de la izquierda para comenzar."
        )
        return

    force_refresh = st.session_state.pop("force_refresh", False)

    with st.spinner(f"Cargando datos de {ticker}..."):
        try:
            stock_service = DataAggregator(ticker, cache_repo=cache_repo)
            calculator = FinancialCalculator()
            info = stock_service.get_info(force_refresh=force_refresh)

            if info.price is None:
                st.error(f"No se pudo encontrar el precio para: {ticker}")
                return

            st.title(f"{info.short_name} ({ticker})")

            metrics = calculator.compute(
                financials=stock_service.get_financials(force_refresh=force_refresh),
                balance=stock_service.get_balance_sheet(force_refresh=force_refresh),
                cashflow=stock_service.get_cashflow(force_refresh=force_refresh),
                pe_ratio=info.pe_ratio,
            )

            tabs = [
                SummaryTab(title="📊 Resumen"),
                FinancialsTab(title="📈 Finanzas"),
                PricesTab(title="💰 Precios"),
                TechnicalTab(title="🔬 Análisis Técnico"),
                NewsTab(title="📰 Noticias", logger=logger),
            ]

            st_tabs = st.tabs([t.title for t in tabs])
            for tab, st_tab in zip(tabs, st_tabs):
                with st_tab:
                    tab.safe_render(
                        stock_service=stock_service,
                        info=info,
                        period=period,
                        ticker=ticker,
                        metrics=metrics,
                    )

            logger.info(f"Dashboard actualizado para {ticker}")

        except Exception as e:
            st.error(f"Error al obtener datos: {str(e)}")
            logger.error(f"Error en main: {str(e)}")


if __name__ == "__main__":
    main()
