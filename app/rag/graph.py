"""Build a semantic similarity graph over the chunks in a collection.

Nodes are chunks; an edge connects two chunks whose embeddings are close in
vector space (cosine similarity). Each node keeps only its ``k`` nearest
neighbours above ``min_sim`` so the graph stays sparse and readable. This is a
lightweight way to *see* the structure the retriever operates on — clusters of
related content, bridges between topics, and where a query lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.embeddings import Embedder
from app.vectorstore import VectorStore


@dataclass
class GraphNode:
    id: str
    label: str
    group: str
    text: str
    degree: int = 0


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float


@dataclass
class SemanticGraph:
    collection: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_semantic_graph(
    vectorstore: VectorStore,
    embedder: Embedder,
    collection: str,
    k: int = 4,
    min_sim: float = 0.15,
    max_nodes: int = 200,
) -> SemanticGraph:
    corpus = vectorstore.iter_corpus(collection)
    if not corpus:
        return SemanticGraph(collection=collection)
    corpus = corpus[:max_nodes]
    by_id = {c.id: c for c in corpus}
    order = [c.id for c in corpus]

    # Prefer stored vectors; otherwise re-embed the chunk texts.
    if hasattr(vectorstore, "get_vectors"):
        ids, matrix = vectorstore.get_vectors(collection)  # type: ignore[attr-defined]
        keep = [(i, cid) for i, cid in enumerate(ids) if cid in by_id]
        rows = [matrix[i] for i, _ in keep]
        order = [cid for _, cid in keep]
        matrix = np.array(rows, dtype=np.float32) if rows else np.zeros((0, 0))
    else:
        matrix = np.array(embedder.embed_documents([by_id[i].text for i in order]))

    if matrix.size == 0:
        return SemanticGraph(collection=collection)

    matrix = _normalize_rows(matrix)
    sims = matrix @ matrix.T
    n = len(order)
    k = min(k, max(n - 1, 1))

    degree: dict[str, int] = {cid: 0 for cid in order}
    seen: set[tuple[str, str]] = set()
    edges: list[GraphEdge] = []
    for i in range(n):
        row = sims[i].copy()
        row[i] = -1.0
        neighbours = np.argsort(-row)[:k]
        for j in neighbours:
            weight = float(row[j])
            if weight < min_sim:
                continue
            a, b = order[i], order[int(j)]
            key = (a, b) if a < b else (b, a)
            if key in seen:
                continue
            seen.add(key)
            edges.append(GraphEdge(source=a, target=b, weight=round(weight, 4)))
            degree[a] += 1
            degree[b] += 1

    nodes = []
    for cid in order:
        chunk = by_id[cid]
        group = chunk.metadata.get("source", "unknown")
        label = f"{group} #{chunk.metadata.get('chunk_index', '?')}"
        nodes.append(
            GraphNode(
                id=cid,
                label=label,
                group=group,
                text=chunk.text,
                degree=degree[cid],
            )
        )
    return SemanticGraph(collection=collection, nodes=nodes, edges=edges)
