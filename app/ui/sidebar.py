"""Componente del sidebar."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import psycopg
import streamlit as st

if TYPE_CHECKING:
    from db.cache_repo import CacheRepository

# Valid ticker: 1-5 uppercase letters, optionally followed by a dot and 1-2 letters (e.g. BRK.B)
_TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")


def render_sidebar(cache_repo: CacheRepository | None = None) -> tuple[str, str]:
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

        # Refresh button for fundamentals
        if ticker:
            if st.button("🔄 Refrescar datos fundamentales", width="stretch"):
                st.session_state["force_refresh"] = True
                st.rerun()

        st.markdown("---")

        # Consulted companies section
        if cache_repo is not None:
            _render_consulted_companies(cache_repo)
        else:
            st.info(
                "Introduce un símbolo de cotización para analizar su rendimiento y estados financieros."
            )

    return ticker, period


def _render_consulted_companies(cache_repo: CacheRepository) -> None:
    """Show recently consulted companies from the database."""
    try:
        companies = cache_repo.get_consulted_companies()
    except psycopg.Error as e:
        import logging

        logging.getLogger(__name__).warning("Failed to load consulted companies: %s", e)
        return

    if not companies:
        st.info("Aún no has consultado ninguna empresa.")
        return

    st.subheader("Empresas consultadas")
    for company in companies:
        ticker = company["ticker"]
        name = company["short_name"] or ticker
        sector = company.get("sector", "")
        label = f"**{ticker}** — {name}"
        if sector:
            label += f"  \n_{sector}_"
        st.markdown(label, unsafe_allow_html=False)
