from __future__ import annotations

import streamlit as st

from typing import Any
import logging
from app.domain.models import StockInfo
from app.domain.services import (
    all_providers,
    available_models,
    workflow,
)
from app.db.cache_repo import CacheRepository
from app.ui.tabs.base import BaseTab

logger = logging.getLogger(__name__)

NODE_LABELS = {
    "collect_data": "📊 Recopilando datos financieros...",
    "research": "🔍 Investigando en fuentes externas...",
    "company": "🏢 Analizando modelo de negocio y competencia...",
    "financials": "📈 Analizando crecimiento, márgenes y FCF...",
    "macro": "🌍 Evaluando entorno macro y valoración...",
    "mgmt": "👔 Generando resumen y recomendación...",
    "synthesize": "📝 Compilando reporte final...",
}


class ResearchTab(BaseTab):
    """Tab para generar research reports."""

    def render(self, **kwargs: Any) -> None:
        """Renderiza el tab de research."""
        info: StockInfo = kwargs["info"]
        cache_repo: CacheRepository | None = kwargs.get("cache_repo")  # type: ignore[assignment]

        cache_key = f"research_{info.ticker}"

        # -- Cargar de PostgreSQL si no está en session_state --------
        if cache_key not in st.session_state and cache_repo is not None:
            cached_report = cache_repo.get_research_report(info.ticker)
            if cached_report:
                st.session_state[cache_key] = cached_report

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
                st.selectbox(
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
            with st.status(
                f"Generando reporte profundo para {info.ticker}...",
                expanded=True,
            ) as status:
                try:
                    # Ejecutar el workflow nodo por nodo con stream
                    last_step: dict[str, dict[str, str]] = {}
                    for step in workflow.stream(  # type: ignore[call-overload]
                        {"ticker": info.ticker}, stream_mode="updates"
                    ):
                        last_step.update(step)
                        for node_name in step:
                            label = NODE_LABELS.get(node_name, node_name)
                            st.write(f"✅ {label}")

                    logger.info(f"Nodos completados: {list(last_step.keys())}")

                    if "synthesize" not in last_step:
                        raise RuntimeError(
                            f"El grafo no llegó al nodo 'synthesize'. "
                            f"Nodos completados: {list(last_step.keys())}"
                        )

                    report_text = last_step["synthesize"]["final_report"]
                    status.update(label="✅ Reporte completado", state="complete")
                    st.session_state[cache_key] = report_text
                    # Persistir en PostgreSQL
                    if cache_repo is not None:
                        cache_repo.upsert_research_report(
                            info.ticker, report_text, str(provider), "workflow"
                        )
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(f"Error: {e}")
                    logger.error(f"Error al generar reporte: {e}")
        # -- Mostrar reporte cacheado ------------------------------------
        elif cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])
