"""Construct the configured vector store."""

from __future__ import annotations

import os

from app.config import Settings

from .base import VectorStore
from .memory_store import MemoryVectorStore


def build_vectorstore(settings: Settings) -> VectorStore:
    backend = settings.vectorstore
    if backend == "memory":
        persist_path = None
        if settings.persist_vectorstore:
            persist_path = os.path.join(settings.data_dir, "memory_store.json")
        return MemoryVectorStore(persist_path=persist_path)
    if backend == "chroma":
        from .chroma_store import ChromaVectorStore

        return ChromaVectorStore(persist_dir=os.path.join(settings.data_dir, "chroma"))
    raise ValueError(f"Unknown vector store backend: {backend!r}")
