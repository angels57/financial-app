"""Componente del sidebar."""

import streamlit as st


def render_sidebar() -> tuple[str, str]:
    """Renderiza el sidebar y retorna (ticker, period)."""
    with st.sidebar:
        st.title("🚀 Financial Stre")
        st.markdown("---")
        ticker = (
            st.text_input("Buscar Ticker:", value="AAPL", placeholder="Ej: AAPL, TSLA")
            .upper()
            .strip()
        )

        st.subheader("Configuración")
        period = st.selectbox(
            "Periodo Histórico", options=["1y", "2y", "5y", "10y", "max"], index=2
        )

        st.markdown("---")
        st.info(
            "Introduce un símbolo de cotización para analizar su rendimiento y estados financieros."
        )

    return ticker, period
