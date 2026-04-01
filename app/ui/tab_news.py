"""Tab de noticias."""

import logging

import streamlit as st

from services import StockService
from ui.base_tab import BaseTab


class NewsTab(BaseTab):
    """Renderiza el tab de noticias — solo depende de StockService (ISP)."""

    def __init__(self, title: str, logger: logging.Logger):
        super().__init__(title)
        self._logger = logger

    def render(self, *, stock_service: StockService, **kwargs) -> None:
        st.subheader(f"Últimas Noticias de {stock_service.ticker}")
        news = stock_service.get_news()

        if not news:
            st.info("No se encontraron noticias recientes para este ticker.")
            return

        for item in news:
            with st.container():
                st.write(f"**{item.title}**")
                st.caption(f"Fuente: {item.publisher} | [Leer más]({item.link})")
                st.markdown("---")
