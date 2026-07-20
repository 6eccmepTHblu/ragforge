"""In-memory vector store with optional JSON persistence.

Zero external services: vectors live in a numpy matrix per collection and
search is an exact cosine similarity. Fine for development, demos, tests and
small corpora (tens of thousands of chunks). Swap in ``ChromaVectorStore`` for
larger, persistent workloads.
"""

from __future__ import annotations

import json
import os
import threading

import numpy as np

from .base import ScoredChunk, VectorRecord, VectorStore


class _Collection:
    def __init__(self) -> None:
        self.ids: list[str] = []
        self.texts: list[str] = []
        self.metadatas: list[dict[str, str]] = []
        self.matrix: np.ndarray | None = None  # shape (n, dim), L2-normalised

    def add(self, records: list[VectorRecord]) -> None:
        new = np.array([r.embedding for r in records], dtype=np.float32)
        new = _normalize(new)
        self.matrix = new if self.matrix is None else np.vstack([self.matrix, new])
        self.ids.extend(r.id for r in records)
        self.texts.extend(r.text for r in records)
        self.metadatas.extend(r.metadata for r in records)


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class MemoryVectorStore(VectorStore):
    supports_corpus_iteration = True

    def __init__(self, persist_path: str | None = None) -> None:
        self._collections: dict[str, _Collection] = {}
        self._persist_path = persist_path
        self._lock = threading.Lock()
        if persist_path and os.path.exists(persist_path):
            self._load()

    @property
    def name(self) -> str:
        return "memory"

    def _get(self, collection: str) -> _Collection:
        return self._collections.setdefault(collection, _Collection())

    def add(self, records: list[VectorRecord], collection: str) -> None:
        if not records:
            return
        with self._lock:
            self._get(collection).add(records)
            self._save()

    def search(
        self, embedding: list[float], top_k: int, collection: str
    ) -> list[ScoredChunk]:
        col = self._collections.get(collection)
        if col is None or col.matrix is None:
            return []
        query = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        scores = col.matrix @ query  # cosine (both sides normalised)
        k = min(top_k, len(scores))
        # argpartition for top-k, then sort just those.
        top_idx = np.argpartition(-scores, k - 1)[:k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]
        return [
            ScoredChunk(
                id=col.ids[i],
                text=col.texts[i],
                score=float(scores[i]),
                metadata=col.metadatas[i],
            )
            for i in top_idx
        ]

    def count(self, collection: str) -> int:
        col = self._collections.get(collection)
        return len(col.ids) if col else 0

    def list_collections(self) -> list[str]:
        return sorted(self._collections.keys())

    def delete_collection(self, collection: str) -> None:
        with self._lock:
            self._collections.pop(collection, None)
            self._save()

    def delete(self, ids: list[str], collection: str) -> int:
        col = self._collections.get(collection)
        if col is None or not ids:
            return 0
        remove = set(ids)
        keep = [i for i, cid in enumerate(col.ids) if cid not in remove]
        removed = len(col.ids) - len(keep)
        if removed == 0:
            return 0
        with self._lock:
            col.ids = [col.ids[i] for i in keep]
            col.texts = [col.texts[i] for i in keep]
            col.metadatas = [col.metadatas[i] for i in keep]
            col.matrix = col.matrix[keep] if (keep and col.matrix is not None) else None
            self._save()
        return removed

    def iter_corpus(self, collection: str) -> list[ScoredChunk]:
        col = self._collections.get(collection)
        if col is None:
            return []
        return [
            ScoredChunk(id=col.ids[i], text=col.texts[i], score=0.0, metadata=col.metadatas[i])
            for i in range(len(col.ids))
        ]

    def get_vectors(self, collection: str) -> tuple[list[str], np.ndarray]:
        """Return ``(ids, matrix)`` of L2-normalised vectors for graph building."""
        col = self._collections.get(collection)
        if col is None or col.matrix is None:
            return [], np.zeros((0, 0), dtype=np.float32)
        return list(col.ids), col.matrix.copy()

    # --- persistence -----------------------------------------------------
    def _save(self) -> None:
        if not self._persist_path:
            return
        os.makedirs(os.path.dirname(self._persist_path) or ".", exist_ok=True)
        payload = {
            name: {
                "ids": col.ids,
                "texts": col.texts,
                "metadatas": col.metadatas,
                "matrix": col.matrix.tolist() if col.matrix is not None else [],
            }
            for name, col in self._collections.items()
        }
        tmp = f"{self._persist_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        os.replace(tmp, self._persist_path)

    def _load(self) -> None:
        with open(self._persist_path, encoding="utf-8") as fh:  # type: ignore[arg-type]
            payload = json.load(fh)
        for name, data in payload.items():
            col = _Collection()
            col.ids = data["ids"]
            col.texts = data["texts"]
            col.metadatas = data["metadatas"]
            matrix = data.get("matrix") or []
            col.matrix = np.array(matrix, dtype=np.float32) if matrix else None
            self._collections[name] = col
