"""Shared pytest fixtures.

Everything here runs fully offline: mock LLM, deterministic hash embeddings and
an in-memory vector store. No API keys, no network, no external services.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import Container, build_container, get_container
from app.main import create_app

DOC_RAG = (
    "Retrieval-Augmented Generation combines a retriever with a large language "
    "model. The retriever finds relevant chunks from a knowledge base using "
    "embeddings and semantic search over a vector database. The language model "
    "then generates a grounded answer conditioned on the retrieved context."
)
DOC_FASTAPI = (
    "FastAPI is a modern Python web framework for building APIs. It relies on "
    "type hints and Pydantic for validation and supports asynchronous request "
    "handling with high performance."
)
DOC_DOCKER = (
    "Docker packages an application and its dependencies into a container image. "
    "Containers run consistently across environments, which simplifies "
    "deployment of microservices."
)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        data_dir=str(tmp_path),
        persist_vectorstore=False,
        llm_provider="mock",
        embedding_provider="hash",
        hash_embedding_dim=256,
        vectorstore="memory",
        chunk_size=128,
        chunk_overlap=16,
        top_k=3,
    )


@pytest.fixture
def container(settings: Settings) -> Container:
    c = build_container(settings)
    c.pipeline.ingest_text(DOC_RAG, collection="default", metadata={"source": "rag.md"})
    c.pipeline.ingest_text(
        DOC_FASTAPI, collection="default", metadata={"source": "fastapi.md"}
    )
    c.pipeline.ingest_text(
        DOC_DOCKER, collection="default", metadata={"source": "docker.md"}
    )
    return c


@pytest.fixture
def client(container: Container) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_container] = lambda: container
    return TestClient(app)
