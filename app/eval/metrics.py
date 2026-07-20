"""Offline retrieval-quality metrics.

These measure the *retriever* independently of the LLM, using a small labelled
set of ``(query, relevant_chunk_ids)`` pairs. Cheap, deterministic and ideal
for regression-testing retrieval changes in CI.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.retrieval import Retriever


def hit_rate_at_k(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    return 1.0 if any(rid in relevant_ids for rid in retrieved_ids) else 0.0


def mrr_at_k(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


@dataclass
class RetrievalReport:
    n: int
    hit_rate: float
    mrr: float


def evaluate_retrieval(
    retriever: Retriever,
    dataset: list[dict],
    collection: str,
    k: int = 5,
) -> RetrievalReport:
    """``dataset`` items: ``{"query": str, "relevant_ids": list[str]}``."""
    if not dataset:
        return RetrievalReport(n=0, hit_rate=0.0, mrr=0.0)

    hits, mrrs = 0.0, 0.0
    for item in dataset:
        relevant = set(item["relevant_ids"])
        results = retriever.retrieve(item["query"], collection=collection, top_k=k)
        ids = [r.id for r in results]
        hits += hit_rate_at_k(ids, relevant)
        mrrs += mrr_at_k(ids, relevant)

    n = len(dataset)
    return RetrievalReport(n=n, hit_rate=hits / n, mrr=mrrs / n)
