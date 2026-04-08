"""Main application entry point."""

import psycopg
import streamlit as st
from yfinance.exceptions import YFException

from app.config import settings
from app.core import get_app_logger, init_monitoring
from app.db import get_pool, init_db
from app.db.cache_repo import CacheRepository
from app.domain.services import FinancialCalculator
from app.infrastructure.yfinance import YFinanceClient
from app.ui import (
    NewsTab,
    OverviewTab,
    PricesTab,
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
    st.markdown(
        """
        <style>
        div[data-testid="stSpinner"] {
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(14, 17, 23, 0.75);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            margin: 0;
            padding: 0;
        }
        div[data-testid="stSpinner"] > div {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
            color: #fafafa;
            font-size: 1.1rem;
            font-weight: 500;
        }
        div[data-testid="stSpinner"] i {
            width: 3rem !important;
            height: 3rem !important;
            border-width: 4px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
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
            stock_service = YFinanceClient(ticker, cache_repo=cache_repo)
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
                OverviewTab(title="📊 Overview"),
                PricesTab(title="💰 Precios"),
                TechnicalTab(title="🔬 Análisis Técnico"),
                NewsTab(title="📰 Noticias"),
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

        except (YFException, psycopg.Error, KeyError, ValueError) as e:
            st.error(f"Error al obtener datos: {str(e)}")
            logger.error(f"Error en main: {str(e)}")


if __name__ == "__main__":
    main()
