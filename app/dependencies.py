"""Dependency wiring.

Builds the object graph once and hands it to the API via FastAPI's dependency
system. Tests build their own :class:`Container` with offline components and
override ``get_container``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from app.config import Settings, get_settings
from app.core import IngestionPipeline, TextSplitter
from app.embeddings import Embedder, build_embedder
from app.eval import AnswerJudge
from app.llm import LLMProvider, build_llm
from app.rag import RAGEngine
from app.retrieval import Retriever
from app.vectorstore import VectorStore, build_vectorstore


@dataclass
class Container:
    settings: Settings
    splitter: TextSplitter
    embedder: Embedder
    vectorstore: VectorStore
    pipeline: IngestionPipeline
    retriever: Retriever
    llm: LLMProvider
    rag_engine: RAGEngine
    judge: AnswerJudge


def build_container(settings: Settings) -> Container:
    os.makedirs(settings.data_dir, exist_ok=True)
    splitter = TextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    embedder = build_embedder(settings)
    vectorstore = build_vectorstore(settings)
    pipeline = IngestionPipeline(splitter, embedder, vectorstore)
    retriever = Retriever(vectorstore, embedder, settings)
    llm = build_llm(settings)
    rag_engine = RAGEngine(retriever, llm, settings)
    judge = AnswerJudge(llm)
    return Container(
        settings=settings,
        splitter=splitter,
        embedder=embedder,
        vectorstore=vectorstore,
        pipeline=pipeline,
        retriever=retriever,
        llm=llm,
        rag_engine=rag_engine,
        judge=judge,
    )


@lru_cache
def get_container() -> Container:
    return build_container(get_settings())
