"""Token-aware recursive text splitter.

Implemented from scratch (rather than importing LangChain) so the chunking
behaviour is explicit and testable. Length is measured in **tokens** via
``tiktoken`` when available, falling back to a whitespace approximation. The
recursive strategy tries to split on progressively finer separators
(paragraph -> line -> sentence -> word -> character) so chunks respect natural
boundaries while staying under ``chunk_size`` tokens, with ``chunk_overlap``
tokens carried between neighbours to preserve context across boundaries.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

_DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@lru_cache(maxsize=1)
def _get_encoder():
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:  # pragma: no cover - fallback path
        return None


def token_length(text: str) -> int:
    encoder = _get_encoder()
    if encoder is not None:
        return len(encoder.encode(text))
    # Fallback: rough word-based estimate.
    return max(1, len(text.split())) if text.strip() else 0


class TextSplitter:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        length_function: Callable[[str], int] = token_length,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._len = length_function
        self._separators = separators or _DEFAULT_SEPARATORS

    def split(self, text: str) -> list[str]:
        chunks = self._split(text, self._separators)
        return [c.strip() for c in chunks if c.strip()]

    # --- internals -------------------------------------------------------
    def _split(self, text: str, separators: list[str]) -> list[str]:
        final: list[str] = []
        separator = separators[-1]
        remaining = separators[:]
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                remaining = []
                break
            if sep in text:
                separator = sep
                remaining = separators[i + 1 :]
                break

        splits = list(text) if separator == "" else text.split(separator)
        merge_sep = "" if separator == "" else separator

        good: list[str] = []
        for piece in splits:
            if self._len(piece) < self.chunk_size:
                good.append(piece)
                continue
            if good:
                final.extend(self._merge(good, merge_sep))
                good = []
            if not remaining:
                final.append(piece)
            else:
                final.extend(self._split(piece, remaining))
        if good:
            final.extend(self._merge(good, merge_sep))
        return final

    def _merge(self, splits: list[str], separator: str) -> list[str]:
        sep_len = self._len(separator)
        docs: list[str] = []
        current: list[str] = []
        total = 0
        for piece in splits:
            piece_len = self._len(piece)
            added = piece_len + (sep_len if current else 0)
            if total + added > self.chunk_size and current:
                docs.append(separator.join(current).strip())
                # Trim from the front until we're back under the overlap budget.
                while current and (
                    total > self.chunk_overlap
                    or (total + added > self.chunk_size and total > 0)
                ):
                    total -= self._len(current[0]) + (sep_len if len(current) > 1 else 0)
                    current = current[1:]
            current.append(piece)
            total += piece_len + (sep_len if len(current) > 1 else 0)
        if current:
            docs.append(separator.join(current).strip())
        return [d for d in docs if d]
