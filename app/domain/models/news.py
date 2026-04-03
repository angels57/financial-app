"""Domain models for news data."""

from pydantic import BaseModel


class NewsItem(BaseModel):
    """Noticia de una acción."""

    title: str
    link: str
    publisher: str = "Fuente desconocida"
    thumbnail: str = ""
    published_at: str = ""
