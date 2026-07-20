"""Document- and chunk-level management: list documents, delete records."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, Query

from app.dependencies import Container, get_container
from app.schemas import DeleteResponse, DocumentInfo, DocumentsResponse

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=DocumentsResponse)
def list_documents(
    collection: str | None = None, container: Container = Depends(get_container)
) -> DocumentsResponse:
    """Group a collection's chunks by their source document."""
    target = collection or container.settings.default_collection
    counts: Counter[str] = Counter(
        chunk.metadata.get("source", "unknown")
        for chunk in container.vectorstore.iter_corpus(target)
    )
    documents = [
        DocumentInfo(source=source, chunks=n) for source, n in sorted(counts.items())
    ]
    return DocumentsResponse(collection=target, documents=documents)


@router.delete("/documents", response_model=DeleteResponse)
def delete_document(
    source: str = Query(..., description="Source name whose chunks to delete."),
    collection: str | None = None,
    container: Container = Depends(get_container),
) -> DeleteResponse:
    """Delete every chunk belonging to a given source document."""
    target = collection or container.settings.default_collection
    ids = [
        chunk.id
        for chunk in container.vectorstore.iter_corpus(target)
        if chunk.metadata.get("source", "unknown") == source
    ]
    deleted = container.vectorstore.delete(ids, collection=target)
    return DeleteResponse(collection=target, deleted=deleted)


@router.delete("/chunks/{chunk_id}", response_model=DeleteResponse)
def delete_chunk(
    chunk_id: str,
    collection: str | None = None,
    container: Container = Depends(get_container),
) -> DeleteResponse:
    """Delete a single chunk by its id."""
    target = collection or container.settings.default_collection
    deleted = container.vectorstore.delete([chunk_id], collection=target)
    return DeleteResponse(collection=target, deleted=deleted)
