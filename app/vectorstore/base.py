"""Vector store interface and shared record types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VectorRecord:
    """A chunk plus its embedding, ready to be stored."""

    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ScoredChunk:
    """A retrieval hit."""

    id: str
    text: str
    score: float
    metadata: dict[str, str] = field(default_factory=dict)


class VectorStore(ABC):
    """Abstract vector database."""

    #: Whether the backend can stream its full corpus back (needed for the
    #: sparse/BM25 leg of hybrid retrieval).
    supports_corpus_iteration: bool = False

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def add(self, records: list[VectorRecord], collection: str) -> None: ...

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        top_k: int,
        collection: str,
    ) -> list[ScoredChunk]: ...

    @abstractmethod
    def count(self, collection: str) -> int: ...

    @abstractmethod
    def list_collections(self) -> list[str]: ...

    @abstractmethod
    def delete_collection(self, collection: str) -> None: ...

    @abstractmethod
    def delete(self, ids: list[str], collection: str) -> int:
        """Delete records by id. Returns the number actually removed."""

    def iter_corpus(self, collection: str) -> list[ScoredChunk]:
        """Return every stored chunk (score is 0.0). Optional capability."""
        raise NotImplementedError(
            f"{self.name} does not support corpus iteration; disable hybrid search."
        )
