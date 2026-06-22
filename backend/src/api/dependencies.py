"""API dependency injectors."""

from functools import lru_cache

from src.config import Settings
from src.llm.provider import OllamaClient


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton (reads config.yaml + .env)."""
    return Settings()


def get_ollama() -> OllamaClient:
    """Build an OllamaClient from settings (one per request)."""
    return OllamaClient(get_settings())
