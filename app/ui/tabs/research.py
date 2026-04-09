from __future__ import annotations

import streamlit as st

from typing import Any
import logging
from app.domain.models import StockInfo, FinancialMetrics
from app.domain.services import research_service, all_providers, available_models
from app.ui.tabs.base import BaseTab
from app.utils import format_large_number

logger = logging.getLogger(__name__)


class ResearchTab(BaseTab):
    """Tab para generar research reports."""

    def render(self, **kwargs: Any) -> None:
        """Renderiza el tab de research."""
        info: StockInfo = kwargs["info"]
        metrics: FinancialMetrics = kwargs["metrics"]

        cache_key = f"research_{info.ticker}"

        # -- Selector de modelo ------------------------------------------
        with st.expander("⚙️  Configurar modelo", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                provider = st.selectbox(
                    "Provider",
                    options=all_providers(),
                    index=0,
                    key="research_provider_select",
                )
            with col2:
                model = st.selectbox(
                    "Modelo",
                    options=available_models(provider),
                    key=f"research_model_select_{provider}",
                )
        # -- Botón de generación -----------------------------------------
        col_btn, col_clear = st.columns([3, 1])
        with col_btn:
            generate = st.button(
                f"Generar Research Report — {info.ticker}",
                type="primary",
                use_container_width=True,
                disabled=cache_key in st.session_state,
            )
        with col_clear:
            if cache_key in st.session_state:
                if st.button("Regenerar", use_container_width=True):
                    del st.session_state[cache_key]
                    st.rerun()
        # -- Generación con streaming ------------------------------------
        if generate and cache_key not in st.session_state:
            context = self._build_context(info, metrics)
            report_text = ""

            with st.status(
                f"Investigando {info.ticker} con {model}...", expanded=True
            ) as status:
                st.write(f"Provider: `{provider}` · Modelo: `{model}`")
                try:
                    for chunk in research_service.generate_report(
                        ticker=info.ticker,
                        context=context,
                        provider=provider,
                        model=model,
                    ):
                        report_text += chunk
                    status.update(label="Reporte completado", state="complete")
                    st.session_state[cache_key] = report_text
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error: {e}")
                    logger.error(f"Error al generar reporte: {e}")
            placeholder = st.empty()
            placeholder.markdown(report_text)
        # -- Mostrar reporte cacheado ------------------------------------
        elif cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])

    @staticmethod
    def _build_context(info: StockInfo, metrics: FinancialMetrics) -> str:
        return f"""
        Ticker: {info.ticker} | {info.short_name}
        Sector: {info.sector} | País: {info.country}
        Precio: {info.currency} {info.price:,.2f}
        Market Cap: {format_large_number(info.market_cap)}
        P/E: {info.pe_ratio} | EPS: {info.eps}
        Revenue (último año): {metrics.revenue_billions[0] if metrics.revenue_billions else "N/A"}B
        Net Margin: {metrics.net_margin[0] if metrics.net_margin else "N/A"}%
        FCF: {metrics.fcf_billions[0] if metrics.fcf_billions else "N/A"}B
        """
