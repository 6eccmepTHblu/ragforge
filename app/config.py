"""Application configuration.

All settings can be provided via environment variables or a local ``.env``
file (see ``.env.example``). The defaults are chosen so the whole service runs
**offline with zero API keys** — using deterministic hash embeddings, an
in-memory vector store and a mock LLM. Swap the ``*_PROVIDER`` variables to
plug in OpenAI / Anthropic / Chroma without touching any code.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RAGFORGE_",
        extra="ignore",
    )

    # --- General ---------------------------------------------------------
    app_name: str = "RAGForge"
    environment: Literal["dev", "staging", "prod"] = "dev"
    data_dir: str = "./.ragforge_data"

    # --- LLM -------------------------------------------------------------
    llm_provider: Literal["mock", "openai", "anthropic"] = "mock"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 800

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    # --- Embeddings ------------------------------------------------------
    embedding_provider: Literal["hash", "openai"] = "hash"
    # Dimension used by the offline deterministic hash embedder.
    hash_embedding_dim: int = 384

    # --- Vector store ----------------------------------------------------
    vectorstore: Literal["memory", "chroma"] = "memory"
    persist_vectorstore: bool = True

    # --- Chunking --------------------------------------------------------
    chunk_size: int = 512       # tokens
    chunk_overlap: int = 64     # tokens

    # --- Retrieval -------------------------------------------------------
    top_k: int = 4
    use_hybrid: bool = True
    # Number of candidates each retriever contributes before fusion.
    candidate_pool: int = 20
    # Reciprocal-rank-fusion constant.
    rrf_k: int = 60

    @property
    def default_collection(self) -> str:
        return "default"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (safe to call from anywhere)."""
    return Settings()
