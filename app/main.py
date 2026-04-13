"""Main application entry point."""

import psycopg
import streamlit as st
from yfinance.exceptions import YFException

from app.config import settings
from app.core import get_app_logger, init_monitoring
from app.db import get_pool, init_db
from app.db.cache_repo import CacheRepository
from app.infrastructure.yfinance import YFinanceClient
from app.ui import (
    NewsTab,
    OverviewTab,
    PricesTab,
    ResearchTab,
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


def main() -> None:
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

    try:
        stock_service = YFinanceClient(ticker, cache_repo=cache_repo)

        with st.spinner(f"Verificando {ticker}..."):
            info = stock_service.get_info(force_refresh=force_refresh)

        if info.price is None:
            st.error(f"No se pudo encontrar el precio para: {ticker}")
            return

        st.title(f"{info.short_name} ({ticker})")

        tabs = [
            OverviewTab(title="📊 Overview"),
            PricesTab(title="💰 Precios"),
            TechnicalTab(title="🔬 Análisis Técnico"),
            NewsTab(title="📰 Noticias"),
            ResearchTab(title="🔬 Research"),
        ]

        st_tabs = st.tabs([t.title for t in tabs])
        for tab, st_tab in zip(tabs, st_tabs):
            with st_tab:
                tab.safe_render(
                    stock_service=stock_service,
                    info=info,
                    period=period,
                    ticker=ticker,
                    force_refresh=force_refresh,
                    cache_repo=cache_repo,
                )

        logger.info(f"Dashboard actualizado para {ticker}")

    except (YFException, psycopg.Error, KeyError, ValueError) as e:
        st.error(f"Error al obtener datos: {str(e)}")
        logger.error(f"Error en main: {str(e)}")


if __name__ == "__main__":
    main()
