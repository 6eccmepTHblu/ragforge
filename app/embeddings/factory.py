"""Construct the configured embedder."""

from __future__ import annotations

from app.config import Settings

from .base import Embedder
from .hash_embedder import HashEmbedder


def build_embedder(settings: Settings) -> Embedder:
    provider = settings.embedding_provider
    if provider == "hash":
        return HashEmbedder(dimension=settings.hash_embedding_dim)
    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "RAGFORGE_OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai."
            )
        from .openai_embedder import OpenAIEmbedder

        return OpenAIEmbedder(
            api_key=settings.openai_api_key, model=settings.openai_embedding_model
        )
    raise ValueError(f"Unknown embedding provider: {provider!r}")
