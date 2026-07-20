"""Health & readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.dependencies import Container, get_container
from app.schemas import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(container: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        llm_provider=container.llm.name,
        embedding_provider=container.embedder.name,
        vectorstore=container.vectorstore.name,
    )
