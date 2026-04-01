import streamlit as st

from config import settings
from core import get_app_logger, init_monitoring
from services import FinancialCalculator, StockService
from ui import FinancialsTab, NewsTab, SummaryTab, TechnicalTab, render_sidebar

logger = get_app_logger("")


def main():
    st.set_page_config(
        page_title="Financial Stre", layout="wide", initial_sidebar_state="expanded"
    )
    init_monitoring(dsn=settings.sentry_dsn, environment=settings.environment)

    ticker, period = render_sidebar()

    if not ticker:
        st.title("Bienvenido a Financial Stre")
        st.info(
            "Por favor, introduce un ticker en el panel de la izquierda para comenzar."
        )
        return

    with st.spinner(f"Cargando datos de {ticker}..."):
        try:
            stock_service = StockService(ticker)
            calculator = FinancialCalculator()
            info = stock_service.get_info()

            if info.price is None:
                st.error(f"No se pudo encontrar el precio para: {ticker}")
                return

            st.title(f"{info.short_name} ({ticker})")

            metrics = calculator.compute(
                financials=stock_service.get_financials(),
                balance=stock_service.get_balance_sheet(),
                cashflow=stock_service.get_cashflow(),
                pe_ratio=info.pe_ratio,
            )

            tabs = [
                SummaryTab(title="📊 Resumen"),
                FinancialsTab(title="📈 Finanzas"),
                TechnicalTab(title="🔬 Análisis Técnico"),
                NewsTab(title="📰 Noticias", logger=logger),
            ]

            st_tabs = st.tabs([t.title for t in tabs])
            for tab, st_tab in zip(tabs, st_tabs):
                with st_tab:
                    tab.render(
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
