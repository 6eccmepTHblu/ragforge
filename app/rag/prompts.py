"""Prompt templates for RAG generation and evaluation."""

from __future__ import annotations

from app.vectorstore import ScoredChunk

RAG_SYSTEM_PROMPT = (
    "You are a precise assistant. Answer the user's question using ONLY the "
    "information in the provided context. Cite the supporting sources inline "
    "using their bracketed numbers, e.g. [1], [2]. If the context does not "
    "contain the answer, say you don't know rather than guessing."
)


def format_context(chunks: list[ScoredChunk]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown")
        blocks.append(f"[{i}] (source: {source})\n{chunk.text}")
    return "\n\n".join(blocks)


def build_rag_user_prompt(question: str, chunks: list[ScoredChunk]) -> str:
    context = format_context(chunks) if chunks else "(no context retrieved)"
    return f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"


JUDGE_SYSTEM_PROMPT = (
    "You are a strict evaluator of retrieval-augmented answers. You assess two "
    "things on a 0.0-1.0 scale: faithfulness (is every claim supported by the "
    "context?) and answer_relevancy (does the answer address the question?)."
)


def build_judge_prompt(question: str, answer: str, contexts: list[str]) -> str:
    joined = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(contexts, start=1))
    return (
        f"Question:\n{question}\n\n"
        f"Answer:\n{answer}\n\n"
        f"Context:\n{joined}\n\n"
        "Score the answer. Respond ONLY with a JSON object with keys "
        '"faithfulness" (float), "answer_relevancy" (float) and "reasoning" '
        "(string). Do not include any text outside the JSON."
    )
