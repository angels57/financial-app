"""Componente del sidebar."""

import re

import streamlit as st

# Valid ticker: 1-5 uppercase letters, optionally followed by a dot and 1-2 letters (e.g. BRK.B)
_TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")


def render_sidebar() -> tuple[str, str]:
    """Renderiza el sidebar y retorna (ticker, period)."""
    with st.sidebar:
        st.title("🚀 Financial Stre")
        st.markdown("---")
        raw_ticker = (
            st.text_input("Buscar Ticker:", value="AAPL", placeholder="Ej: AAPL, TSLA")
            .upper()
            .strip()
        )

        ticker = raw_ticker
        if raw_ticker and not _TICKER_PATTERN.match(raw_ticker):
            st.warning("Ticker inválido. Usa entre 1-5 letras (ej: AAPL, TSLA, BRK.B).")
            ticker = ""

        st.subheader("Configuración")
        period = st.selectbox(
            "Periodo Histórico", options=["1y", "2y", "5y", "10y", "max"], index=2
        )

        st.markdown("---")
        st.info(
            "Introduce un símbolo de cotización para analizar su rendimiento y estados financieros."
        )

    return ticker, period
