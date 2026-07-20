"""Ingestion pipeline: documents -> chunks -> embeddings -> vector store."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.embeddings import Embedder
from app.vectorstore import VectorRecord, VectorStore

from .chunking import TextSplitter
from .documents import Document

# Stable namespace so identical (source, index, text) triples map to the same id.
_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")


@dataclass
class IngestResult:
    collection: str
    documents: int
    chunks: int


class IngestionPipeline:
    def __init__(
        self,
        splitter: TextSplitter,
        embedder: Embedder,
        vectorstore: VectorStore,
    ) -> None:
        self._splitter = splitter
        self._embedder = embedder
        self._store = vectorstore

    def ingest_documents(
        self, documents: list[Document], collection: str
    ) -> IngestResult:
        records: list[VectorRecord] = []
        for doc in documents:
            source = doc.metadata.get("source", "inline")
            chunks = self._splitter.split(doc.text)
            if not chunks:
                continue
            embeddings = self._embedder.embed_documents(chunks)
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=True)):
                chunk_id = str(uuid.uuid5(_NAMESPACE, f"{source}:{idx}:{chunk}"))
                metadata = {**doc.metadata, "chunk_index": str(idx)}
                records.append(
                    VectorRecord(
                        id=chunk_id, text=chunk, embedding=emb, metadata=metadata
                    )
                )
        self._store.add(records, collection=collection)
        return IngestResult(
            collection=collection, documents=len(documents), chunks=len(records)
        )

    def ingest_text(
        self, text: str, collection: str, metadata: dict[str, str] | None = None
    ) -> IngestResult:
        doc = Document(text=text, metadata=metadata or {})
        return self.ingest_documents([doc], collection=collection)
