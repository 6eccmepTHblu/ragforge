"""ChromaDB vector store backend (optional, requires ``chromadb``).

Enable with ``RAGFORGE_VECTORSTORE=chroma``. Data is persisted on disk under
``<data_dir>/chroma``. We pass pre-computed embeddings explicitly so Chroma
never runs its own embedding function — the configured :class:`Embedder`
stays the single source of truth.
"""

from __future__ import annotations

from .base import ScoredChunk, VectorRecord, VectorStore


class ChromaVectorStore(VectorStore):
    supports_corpus_iteration = True

    def __init__(self, persist_dir: str) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'chromadb' package is required for the Chroma backend. "
                "Install it with `pip install chromadb`."
            ) from exc

        self._client = chromadb.PersistentClient(path=persist_dir)

    @property
    def name(self) -> str:
        return "chroma"

    def _collection(self, collection: str):
        return self._client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}
        )

    def add(self, records: list[VectorRecord], collection: str) -> None:
        if not records:
            return
        col = self._collection(collection)
        col.add(
            ids=[r.id for r in records],
            documents=[r.text for r in records],
            embeddings=[r.embedding for r in records],
            metadatas=[r.metadata or {"_": ""} for r in records],
        )

    def search(
        self, embedding: list[float], top_k: int, collection: str
    ) -> list[ScoredChunk]:
        col = self._collection(collection)
        n = min(top_k, max(col.count(), 1))
        res = col.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        out: list[ScoredChunk] = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for id_, doc, meta, dist in zip(ids, docs, metas, dists, strict=False):
            out.append(
                ScoredChunk(
                    id=id_,
                    text=doc,
                    score=1.0 - float(dist),  # cosine distance -> similarity
                    metadata={k: str(v) for k, v in (meta or {}).items() if k != "_"},
                )
            )
        return out

    def count(self, collection: str) -> int:
        return self._collection(collection).count()

    def list_collections(self) -> list[str]:
        return sorted(c.name for c in self._client.list_collections())

    def delete_collection(self, collection: str) -> None:
        try:
            self._client.delete_collection(collection)
        except Exception:  # noqa: BLE001 - deleting a missing collection is a no-op
            pass

    def delete(self, ids: list[str], collection: str) -> int:
        if not ids:
            return 0
        col = self._collection(collection)
        before = col.count()
        col.delete(ids=ids)
        return before - col.count()

    def iter_corpus(self, collection: str) -> list[ScoredChunk]:
        col = self._collection(collection)
        data = col.get(include=["documents", "metadatas"])
        ids = data.get("ids", [])
        docs = data.get("documents", [])
        metas = data.get("metadatas", [])
        return [
            ScoredChunk(
                id=id_,
                text=doc,
                score=0.0,
                metadata={k: str(v) for k, v in (meta or {}).items() if k != "_"},
            )
            for id_, doc, meta in zip(ids, docs, metas, strict=False)
        ]
