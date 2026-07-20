"""RAG engine: retrieve -> assemble prompt -> generate."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass, field

from app.config import Settings
from app.llm import LLMProvider, system, user
from app.retrieval import Retriever
from app.vectorstore import ScoredChunk

from .prompts import RAG_SYSTEM_PROMPT, build_rag_user_prompt


@dataclass
class RAGAnswer:
    question: str
    answer: str
    collection: str
    sources: list[ScoredChunk] = field(default_factory=list)
    latency_ms: float = 0.0


class RAGEngine:
    def __init__(
        self, retriever: Retriever, llm: LLMProvider, settings: Settings
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._settings = settings

    def _messages(self, question: str, chunks: list[ScoredChunk]):
        return [
            system(RAG_SYSTEM_PROMPT),
            user(build_rag_user_prompt(question, chunks)),
        ]

    def answer(
        self, question: str, collection: str, top_k: int | None = None
    ) -> RAGAnswer:
        started = time.perf_counter()
        chunks = self._retriever.retrieve(question, collection=collection, top_k=top_k)
        text = self._llm.generate(
            self._messages(question, chunks),
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
        )
        latency = (time.perf_counter() - started) * 1000
        return RAGAnswer(
            question=question,
            answer=text.strip(),
            collection=collection,
            sources=chunks,
            latency_ms=round(latency, 2),
        )

    def stream_answer(
        self, question: str, collection: str, top_k: int | None = None
    ) -> tuple[list[ScoredChunk], Iterator[str]]:
        """Return the retrieved sources and a token iterator for the answer."""
        chunks = self._retriever.retrieve(question, collection=collection, top_k=top_k)
        tokens = self._llm.stream(
            self._messages(question, chunks),
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
        )
        return chunks, tokens
