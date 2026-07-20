"""OpenAI chat backend (optional)."""

from __future__ import annotations

from collections.abc import Iterator

from .base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'openai' package is required for the OpenAI provider."
            ) from exc
        self._client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def generate(
        self, messages: list[Message], temperature: float = 0.1, max_tokens: int = 800
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def stream(
        self, messages: list[Message], temperature: float = 0.1, max_tokens: int = 800
    ) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
