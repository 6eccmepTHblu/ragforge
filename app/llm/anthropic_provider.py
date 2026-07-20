"""Anthropic (Claude) chat backend (optional).

Anthropic's Messages API takes the system prompt as a top-level argument
rather than a message with ``role=system``, so we split it out here.
"""

from __future__ import annotations

from collections.abc import Iterator

from .base import LLMProvider, Message


def _split_system(messages: list[Message]) -> tuple[str, list[Message]]:
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    convo = [m for m in messages if m["role"] != "system"]
    return "\n\n".join(system_parts), convo


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-5") -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'anthropic' package is required for the Anthropic provider."
            ) from exc
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return f"anthropic:{self._model}"

    def generate(
        self, messages: list[Message], temperature: float = 0.1, max_tokens: int = 800
    ) -> str:
        system_prompt, convo = _split_system(messages)
        response = self._client.messages.create(
            model=self._model,
            system=system_prompt or None,
            messages=convo,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def stream(
        self, messages: list[Message], temperature: float = 0.1, max_tokens: int = 800
    ) -> Iterator[str]:
        system_prompt, convo = _split_system(messages)
        with self._client.messages.stream(
            model=self._model,
            system=system_prompt or None,
            messages=convo,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            yield from stream.text_stream
