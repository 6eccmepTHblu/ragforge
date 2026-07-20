"""A small, dependency-free BM25 (Okapi) index for sparse lexical retrieval.

Dense embeddings capture semantics but can miss exact terms (names, codes,
rare keywords). BM25 covers that blind spot; fusing the two (see
:mod:`app.retrieval.hybrid`) is a well-established recipe for stronger recall.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-Я0-9]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._doc_tokens: list[list[str]] = []
        self._doc_len: list[int] = []
        self._doc_freqs: list[Counter[str]] = []
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0

    def build(self, documents: list[str]) -> BM25Index:
        self._doc_tokens = [tokenize(d) for d in documents]
        self._doc_len = [len(t) for t in self._doc_tokens]
        self._doc_freqs = [Counter(t) for t in self._doc_tokens]
        n = len(self._doc_tokens)
        self._avgdl = (sum(self._doc_len) / n) if n else 0.0

        df: Counter[str] = Counter()
        for freqs in self._doc_freqs:
            df.update(freqs.keys())
        self._idf = {
            term: math.log(1 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }
        return self

    def scores(self, query: str) -> list[float]:
        q_terms = tokenize(query)
        out = [0.0] * len(self._doc_tokens)
        if not self._doc_tokens:
            return out
        for i, freqs in enumerate(self._doc_freqs):
            dl = self._doc_len[i]
            denom_norm = self.k1 * (1 - self.b + self.b * dl / (self._avgdl or 1))
            score = 0.0
            for term in q_terms:
                if term not in freqs:
                    continue
                f = freqs[term]
                idf = self._idf.get(term, 0.0)
                score += idf * (f * (self.k1 + 1)) / (f + denom_norm)
            out[i] = score
        return out

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        scored = list(enumerate(self.scores(query)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(i, s) for i, s in scored[:top_k] if s > 0.0]
