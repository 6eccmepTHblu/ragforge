"""Pydantic request/response models exposed by the HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Ingestion -----------------------------------------------------------
class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw document text to index.")
    collection: str | None = Field(None, description="Target collection name.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Arbitrary metadata attached to every chunk."
    )
    source: str | None = Field(None, description="Human-readable source identifier.")


class IngestResponse(BaseModel):
    collection: str
    documents: int
    chunks: int


# --- Search / Retrieval --------------------------------------------------
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str | None = None
    top_k: int | None = Field(None, ge=1, le=50)


class SourceChunk(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, str] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    collection: str
    results: list[SourceChunk]


# --- RAG query -----------------------------------------------------------
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    collection: str | None = None
    top_k: int | None = Field(None, ge=1, le=50)


class QueryResponse(BaseModel):
    question: str
    answer: str
    collection: str
    sources: list[SourceChunk]
    latency_ms: float


# --- Collections ---------------------------------------------------------
class CollectionInfo(BaseModel):
    name: str
    chunks: int


class CollectionsResponse(BaseModel):
    collections: list[CollectionInfo]


# --- Evaluation ----------------------------------------------------------
class JudgeRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]


class JudgeResponse(BaseModel):
    faithfulness: float
    answer_relevancy: float
    reasoning: str


# --- Documents & deletion ------------------------------------------------
class DocumentInfo(BaseModel):
    source: str
    chunks: int


class DocumentsResponse(BaseModel):
    collection: str
    documents: list[DocumentInfo]


class DeleteResponse(BaseModel):
    collection: str
    deleted: int


# --- Knowledge graph -----------------------------------------------------
class GraphNodeModel(BaseModel):
    id: str
    label: str
    group: str
    text: str
    degree: int


class GraphEdgeModel(BaseModel):
    source: str
    target: str
    weight: float


class GraphResponse(BaseModel):
    collection: str
    nodes: list[GraphNodeModel]
    edges: list[GraphEdgeModel]


# --- Health --------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    embedding_provider: str
    vectorstore: str
