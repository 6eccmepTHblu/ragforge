"""Ingestion endpoints: index raw text or an uploaded file."""

from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core import load_file
from app.dependencies import Container, get_container
from app.schemas import IngestResponse, IngestTextRequest

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/text", response_model=IngestResponse)
def ingest_text(
    payload: IngestTextRequest, container: Container = Depends(get_container)
) -> IngestResponse:
    collection = payload.collection or container.settings.default_collection
    metadata = dict(payload.metadata)
    if payload.source:
        metadata.setdefault("source", payload.source)
    result = container.pipeline.ingest_text(
        payload.text, collection=collection, metadata=metadata
    )
    return IngestResponse(
        collection=result.collection, documents=result.documents, chunks=result.chunks
    )


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    collection: str | None = Form(None),
    container: Container = Depends(get_container),
) -> IngestResponse:
    target_collection = collection or container.settings.default_collection
    suffix = os.path.splitext(file.filename or "upload.txt")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        document = load_file(tmp_path)
        document.metadata["source"] = file.filename or document.metadata.get("source", "upload")
        result = container.pipeline.ingest_documents(
            [document], collection=target_collection
        )
    finally:
        os.unlink(tmp_path)
    return IngestResponse(
        collection=result.collection, documents=result.documents, chunks=result.chunks
    )
