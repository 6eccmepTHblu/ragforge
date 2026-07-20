"""Embedder interface.

An embedder turns text into dense vectors. Keeping this behind an abstract
base class lets the rest of the system stay agnostic to *how* embeddings are
produced (a local deterministic model, OpenAI, a sentence-transformer, ...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract embedding model."""

    #: Dimensionality of the produced vectors.
    dimension: int

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier of the embedder (used in health checks/logs)."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query. Defaults to the document path."""
        return self.embed_documents([text])[0]
