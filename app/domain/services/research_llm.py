from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from typing import cast
from app.config.settings import settings

logger = logging.getLogger(__name__)

_PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "ollama": ["llama3.1", "llama3.2", "qwen2.5", "mistral"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
    "huggingface": [
        "meta-llama/Llama-3.1-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
    ],
}


def get_llm(provider: str | None = None, model: str | None = None) -> BaseChatModel:
    """Factory que devuelve el LLM según provider y modelo."""

    provider = provider or settings.research_provider
    model = model or settings.research_model

    match provider:
        case "ollama":
            from langchain_ollama import ChatOllama

            logger.info(f"Usando Ollama con modelo: {model}")

            return cast(
                BaseChatModel,
                ChatOllama(
                    model=model,
                    temperature=settings.research_temperature,
                    num_ctx=32000,
                ),
            )

        case "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            logger.info(f"Usando Gemini con modelo: {model}")

            return cast(
                BaseChatModel,
                ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=settings.gemini_api_key,
                    temperature=settings.research_temperature,
                ),
            )

        case "openai":
            from langchain_openai import ChatOpenAI

            logger.info(f"Usando OpenAI con modelo: {model}")

            return cast(
                BaseChatModel,
                ChatOpenAI(
                    model=model,
                    api_key=settings.openai_api_key,
                    temperature=settings.research_temperature,
                ),
            )

        case "huggingface":
            from langchain_huggingface import HuggingFaceEndpoint

            logger.info(f"Usando HuggingFace con modelo: {model}")

            return cast(
                BaseChatModel,
                HuggingFaceEndpoint(
                    model=model,
                    huggingfacehub_api_token=settings.hf_token,
                    temperature=settings.research_temperature,
                ),
            )

        case _:
            raise ValueError(f"Provider desconocido: {provider}")


def available_models(provider: str) -> list[str]:
    return _PROVIDER_MODELS.get(provider, [])


def all_providers() -> list[str]:
    return list(_PROVIDER_MODELS.keys())
