"""Clase base abstracta para los tabs del dashboard."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import streamlit as st

logger = logging.getLogger(__name__)


class BaseTab(ABC):
    """Interfaz común para todos los tabs — Open/Closed principle."""

    def __init__(self, title: str) -> None:
        self.title = title

    def safe_render(self, **kwargs: object) -> None:
        """Render with error boundary and loading spinner — prevents one tab from crashing the whole app."""
        with st.spinner(f"Cargando {self.title}..."):
            try:
                self.render(**kwargs)
            except Exception as e:
                st.error(f"Error al renderizar {self.title}: {e}")
                logger.exception("Error rendering tab %s", self.title)

    @abstractmethod
    def render(self, **kwargs: object) -> None: ...
