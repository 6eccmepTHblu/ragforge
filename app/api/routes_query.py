"""Retrieval and RAG query endpoints."""

from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.dependencies import Container, get_container
from app.schemas import (
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SourceChunk,
)
from app.vectorstore import ScoredChunk

router = APIRouter(tags=["query"])


def _to_sources(chunks: list[ScoredChunk]) -> list[SourceChunk]:
    return [
        SourceChunk(id=c.id, text=c.text, score=round(c.score, 6), metadata=c.metadata)
        for c in chunks
    ]


@router.post("/search", response_model=SearchResponse)
def search(
    payload: SearchRequest, container: Container = Depends(get_container)
) -> SearchResponse:
    collection = payload.collection or container.settings.default_collection
    chunks = container.retriever.retrieve(
        payload.query, collection=collection, top_k=payload.top_k
    )
    return SearchResponse(
        query=payload.query, collection=collection, results=_to_sources(chunks)
    )


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest, container: Container = Depends(get_container)
) -> QueryResponse:
    collection = payload.collection or container.settings.default_collection
    result = container.rag_engine.answer(
        payload.question, collection=collection, top_k=payload.top_k
    )
    return QueryResponse(
        question=result.question,
        answer=result.answer,
        collection=result.collection,
        sources=_to_sources(result.sources),
        latency_ms=result.latency_ms,
    )


@router.post("/query/stream")
def query_stream(
    payload: QueryRequest, container: Container = Depends(get_container)
) -> StreamingResponse:
    """Server-Sent Events: a ``sources`` event, then ``token`` events, then ``done``."""
    collection = payload.collection or container.settings.default_collection
    chunks, tokens = container.rag_engine.stream_answer(
        payload.question, collection=collection, top_k=payload.top_k
    )

    def event_stream() -> Iterator[str]:
        sources = [s.model_dump() for s in _to_sources(chunks)]
        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"
        for token in tokens:
            yield f"event: token\ndata: {json.dumps(token)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
