"""Clase base abstracta para los tabs del dashboard."""

from abc import ABC, abstractmethod


class BaseTab(ABC):
    """Interfaz común para todos los tabs — Open/Closed principle."""

    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def render(self, **kwargs) -> None: ...
