"""Tab de noticias."""

from __future__ import annotations

from typing import Any

import streamlit as st

from domain.services.protocols import StockDataFetcherProtocol
from ui.tabs.base import BaseTab


class NewsTab(BaseTab):
    """Renderiza el tab de noticias — solo depende de StockService (ISP)."""

    def __init__(self, title: str) -> None:
        super().__init__(title)

    def render(self, *, stock_service: StockDataFetcherProtocol, **kwargs: Any) -> None:
        st.subheader(f"Últimas Noticias de {stock_service.ticker}")
        news = stock_service.get_news()

        if not news:
            st.info("No se encontraron noticias recientes para este ticker.")
            return

        for item in news:
            if not item.title or not item.link:
                continue
            with st.container():
                col_img, col_text = st.columns([1, 3])
                with col_img:
                    if item.thumbnail:
                        st.image(item.thumbnail, width="stretch")
                with col_text:
                    st.markdown(f"**[{item.title}]({item.link})**")
                    caption_parts = [f"Fuente: {item.publisher}"]
                    if item.published_at:
                        date_str = item.published_at[:10]
                        caption_parts.append(date_str)
                    st.caption(" | ".join(caption_parts))
                st.markdown("---")
