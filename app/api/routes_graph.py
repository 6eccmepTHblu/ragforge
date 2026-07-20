"""Knowledge-graph endpoint: a semantic similarity graph over a collection."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import Container, get_container
from app.rag.graph import build_semantic_graph
from app.schemas import GraphEdgeModel, GraphNodeModel, GraphResponse

router = APIRouter(tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
def graph(
    collection: str | None = None,
    k: int = Query(4, ge=1, le=15, description="Nearest neighbours per node."),
    min_sim: float = Query(0.15, ge=0.0, le=1.0, description="Minimum edge similarity."),
    max_nodes: int = Query(200, ge=1, le=1000),
    container: Container = Depends(get_container),
) -> GraphResponse:
    target = collection or container.settings.default_collection
    g = build_semantic_graph(
        vectorstore=container.vectorstore,
        embedder=container.embedder,
        collection=target,
        k=k,
        min_sim=min_sim,
        max_nodes=max_nodes,
    )
    return GraphResponse(
        collection=g.collection,
        nodes=[
            GraphNodeModel(
                id=n.id, label=n.label, group=n.group, text=n.text, degree=n.degree
            )
            for n in g.nodes
        ],
        edges=[
            GraphEdgeModel(source=e.source, target=e.target, weight=e.weight)
            for e in g.edges
        ],
    )
