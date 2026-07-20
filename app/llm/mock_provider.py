"""Deterministic offline LLM stand-in.

Lets the entire RAG and evaluation flow run — and be unit-tested — without any
API key or network call. It is intentionally simple: it grounds its "answer"
in the supplied context (so tests can assert the answer reflects retrieved
text) and returns structured JSON when asked to act as an evaluation judge.
"""

from __future__ import annotations

import json
import re

from .base import LLMProvider, Message

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _first_sentences(text: str, n: int = 2) -> str:
    sentences = [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]
    return " ".join(sentences[:n])


class MockLLM(LLMProvider):
    @property
    def name(self) -> str:
        return "mock"

    def generate(
        self, messages: list[Message], temperature: float = 0.1, max_tokens: int = 800
    ) -> str:
        prompt = messages[-1]["content"] if messages else ""

        # Judge mode: the eval prompt asks for a JSON verdict.
        if "faithfulness" in prompt and "JSON" in prompt:
            return json.dumps(
                {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.85,
                    "reasoning": "Deterministic mock judge: answer is grounded in the "
                    "provided context.",
                }
            )

        # RAG mode: ground the answer in the retrieved context block.
        context = prompt
        if "Question:" in prompt:
            context = prompt.split("Question:", 1)[0]
        context = context.replace("Context:", "").strip()
        grounded = _first_sentences(context, n=2) or "No relevant context was found."
        return f"[mock-llm] Based on the retrieved context: {grounded}"
