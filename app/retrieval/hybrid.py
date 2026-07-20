"""Reciprocal Rank Fusion (RRF) for combining ranked lists.

RRF merges results from independent retrievers using only their *ranks*, which
makes it robust to the fact that cosine similarities and BM25 scores live on
different, non-comparable scales. Score for an item = sum over lists of
``1 / (k + rank)``. See Cormack et al., 2009.
"""

from __future__ import annotations


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = 60
) -> dict[str, float]:
    """Return ``{id: fused_score}`` from several ranked lists of ids."""
    fused: dict[str, float] = {}
    for ranking in ranked_lists:
        for rank, item_id in enumerate(ranking):
            fused[item_id] = fused.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return fused
