"""Construct the configured LLM provider."""

from __future__ import annotations

from app.config import Settings

from .base import LLMProvider
from .mock_provider import MockLLM


def build_llm(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider
    if provider == "mock":
        return MockLLM()
    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("RAGFORGE_OPENAI_API_KEY is required for LLM_PROVIDER=openai.")
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "RAGFORGE_ANTHROPIC_API_KEY is required for LLM_PROVIDER=anthropic."
            )
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key, model=settings.anthropic_model
        )
    raise ValueError(f"Unknown LLM provider: {provider!r}")
