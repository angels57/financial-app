"""Componente del sidebar."""

from __future__ import annotations

from typing import TYPE_CHECKING

import psycopg
import streamlit as st

if TYPE_CHECKING:
    from app.db.cache_repo import CacheRepository

from app.domain.validators import validate_ticker


def render_sidebar(cache_repo: CacheRepository | None = None) -> tuple[str, str]:
    """Renderiza el sidebar y retorna (ticker, period)."""
    with st.sidebar:
        st.title("🚀 Financial Stre")
        st.markdown("---")

        default_ticker = st.query_params.get("ticker", "AAPL")
        raw_ticker = (
            st.text_input(
                "Buscar Ticker:",
                value=default_ticker,
                placeholder="Ej: AAPL, TSLA",
            )
            .upper()
            .strip()
        )

        error = validate_ticker(raw_ticker)
        if error:
            st.warning(error)
            ticker = ""
        else:
            ticker = raw_ticker
            st.query_params["ticker"] = ticker

        st.subheader("Configuración")
        period = st.selectbox(
            "Periodo Histórico", options=["1y", "2y", "5y", "10y", "max"], index=2
        )

        if ticker:
            if st.button("🔄 Refrescar datos fundamentales", width="stretch"):
                st.session_state["force_refresh"] = True
                st.rerun()

        st.markdown("---")

        if cache_repo is not None:
            _render_consulted_companies(cache_repo)
        else:
            st.info(
                "Introduce un símbolo de cotización para analizar su rendimiento y estados financieros."
            )

    return ticker, period


def _render_consulted_companies(cache_repo: CacheRepository) -> None:
    """Show recently consulted companies from the database as clickable buttons."""
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
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{ticker}** — {name}")
            if sector:
                st.caption(sector)
        with col2:
            if st.button("→", key=f"goto_{ticker}", help=f"Ver {name} ({ticker})"):
                st.query_params["ticker"] = ticker
                st.session_state["force_refresh"] = True
                st.rerun()
