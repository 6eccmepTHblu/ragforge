"""Retriever: dense vector search, optionally fused with sparse BM25."""

from __future__ import annotations

from app.config import Settings
from app.embeddings import Embedder
from app.vectorstore import ScoredChunk, VectorStore

from .bm25 import BM25Index
from .hybrid import reciprocal_rank_fusion


class Retriever:
    def __init__(
        self, vectorstore: VectorStore, embedder: Embedder, settings: Settings
    ) -> None:
        self._store = vectorstore
        self._embedder = embedder
        self._settings = settings
        # Cache the BM25 index per collection, rebuilt only when size changes.
        self._bm25_cache: dict[str, tuple[int, BM25Index, list[ScoredChunk]]] = {}

    def retrieve(
        self, query: str, collection: str, top_k: int | None = None
    ) -> list[ScoredChunk]:
        k = top_k or self._settings.top_k
        pool = max(self._settings.candidate_pool, k)

        query_emb = self._embedder.embed_query(query)
        dense = self._store.search(query_emb, top_k=pool, collection=collection)

        use_hybrid = (
            self._settings.use_hybrid and self._store.supports_corpus_iteration
        )
        if not use_hybrid:
            return dense[:k]

        bm25, corpus = self._get_bm25(collection)
        if not corpus:
            return dense[:k]

        sparse_hits = bm25.search(query, top_k=pool)
        dense_ranking = [c.id for c in dense]
        sparse_ranking = [corpus[i].id for i, _ in sparse_hits]

        fused = reciprocal_rank_fusion([dense_ranking, sparse_ranking], k=self._settings.rrf_k)
        by_id = {c.id: c for c in corpus}
        for c in dense:  # ensure dense hits are resolvable even if corpus lags
            by_id.setdefault(c.id, c)

        ranked_ids = sorted(fused, key=lambda cid: fused[cid], reverse=True)
        results: list[ScoredChunk] = []
        for cid in ranked_ids[:k]:
            base = by_id.get(cid)
            if base is None:
                continue
            results.append(
                ScoredChunk(
                    id=base.id, text=base.text, score=fused[cid], metadata=base.metadata
                )
            )
        return results

    def _get_bm25(self, collection: str) -> tuple[BM25Index, list[ScoredChunk]]:
        count = self._store.count(collection)
        cached = self._bm25_cache.get(collection)
        if cached and cached[0] == count:
            return cached[1], cached[2]
        corpus = self._store.iter_corpus(collection)
        index = BM25Index().build([c.text for c in corpus])
        self._bm25_cache[collection] = (count, index, corpus)
        return index, corpus
