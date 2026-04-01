"""Tab de análisis técnico."""

import streamlit as st

from ui.base_tab import BaseTab


class TechnicalTab(BaseTab):
    """Renderiza el tab de análisis técnico (en desarrollo)."""

    def render(self, **kwargs) -> None:
        st.subheader("Indicadores Técnicos")
        st.info("Sección en desarrollo. Aquí se mostrarán RSI, MACD y Medias Móviles.")
