"""Collection management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import Container, get_container
from app.schemas import CollectionInfo, CollectionsResponse

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=CollectionsResponse)
def list_collections(
    container: Container = Depends(get_container),
) -> CollectionsResponse:
    names = container.vectorstore.list_collections()
    return CollectionsResponse(
        collections=[
            CollectionInfo(name=name, chunks=container.vectorstore.count(name))
            for name in names
        ]
    )


@router.delete("/{name}")
def delete_collection(
    name: str, container: Container = Depends(get_container)
) -> dict[str, str]:
    container.vectorstore.delete_collection(name)
    return {"status": "deleted", "collection": name}
