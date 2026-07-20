"""LLM provider interface.

A provider takes chat messages (``[{"role": ..., "content": ...}]``) and
returns generated text. Keeping generation behind this interface means the RAG
engine, the evaluation judge and the API never depend on a specific vendor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

Message = dict[str, str]


def system(content: str) -> Message:
    return {"role": "system", "content": content}


def user(content: str) -> Message:
    return {"role": "user", "content": content}


class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> str: ...

    def stream(
        self,
        messages: list[Message],
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        """Token stream. Providers override this; the default yields once."""
        yield self.generate(messages, temperature=temperature, max_tokens=max_tokens)
