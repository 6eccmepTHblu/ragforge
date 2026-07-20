"""Deterministic, dependency-free embedder for offline/dev use.

This is **not** a neural model. It uses the classic *hashing trick* over word
tokens and character n-grams to project text into a fixed-dimensional vector,
then L2-normalises it. Texts that share vocabulary and sub-word structure end
up with a higher cosine similarity, which is enough to exercise the full
retrieval pipeline deterministically — no API keys, no downloads, reproducible
in CI. Point ``RAGFORGE_EMBEDDING_PROVIDER=openai`` at a real model for
production-quality semantics.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

from .base import Embedder

_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-Я0-9]+", re.UNICODE)


def _stable_hash(token: str) -> int:
    """Process-stable hash (Python's built-in ``hash`` is salted per run)."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little")


def _char_ngrams(token: str, n: int = 3) -> list[str]:
    padded = f"#{token}#"
    if len(padded) <= n:
        return [padded]
    return [padded[i : i + n] for i in range(len(padded) - n + 1)]


class HashEmbedder(Embedder):
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    @property
    def name(self) -> str:
        return f"hash-{self.dimension}"

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dimension, dtype=np.float32)
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            features = [token, *_char_ngrams(token)]
            for feat in features:
                h = _stable_hash(feat)
                idx = h % self.dimension
                sign = 1.0 if (h >> 63) & 1 else -1.0
                vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t).tolist() for t in texts]
