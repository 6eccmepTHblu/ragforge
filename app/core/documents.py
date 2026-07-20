"""Document model and lightweight loaders."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Document:
    """A source document prior to chunking."""

    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def load_text_file(path: str) -> Document:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return Document(text=text, metadata={"source": os.path.basename(path)})


def load_pdf_file(path: str) -> Document:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "The 'pypdf' package is required to ingest PDFs. "
            "Install it with `pip install pypdf`."
        ) from exc

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return Document(text="\n\n".join(pages), metadata={"source": os.path.basename(path)})


def load_file(path: str) -> Document:
    """Dispatch to a loader based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return load_pdf_file(path)
    if ext in {".txt", ".md", ".markdown", ".rst", ""}:
        return load_text_file(path)
    # Best effort: treat anything else as UTF-8 text.
    return load_text_file(path)
