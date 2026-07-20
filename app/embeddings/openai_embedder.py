"""OpenAI embedding backend (optional, requires ``openai`` + an API key)."""

from __future__ import annotations

from .base import Embedder

# Native dimensions of common OpenAI embedding models.
_MODEL_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIEmbedder(Embedder):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "The 'openai' package is required for the OpenAI embedder. "
                "Install it with `pip install openai`."
            ) from exc

        self._client = OpenAI(api_key=api_key)
        self._model = model
        self.dimension = _MODEL_DIMS.get(model, 1536)

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # OpenAI rejects empty strings; guard defensively.
        cleaned = [t if t.strip() else " " for t in texts]
        response = self._client.embeddings.create(model=self._model, input=cleaned)
        return [item.embedding for item in response.data]
