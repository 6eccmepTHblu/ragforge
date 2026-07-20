"""End-to-end demo that runs the whole RAG flow offline (no API keys).

Run from the project root:

    python -m scripts.demo

It ingests the sample document, answers a couple of questions with cited
sources, and prints a small retrieval-quality report.
"""

from __future__ import annotations

import os

from app.config import Settings
from app.core import load_file
from app.dependencies import build_container
from app.eval import evaluate_retrieval

SAMPLE = os.path.join(os.path.dirname(__file__), "sample_data", "ai_ml_overview.md")


def main() -> None:
    # Small chunks so the short sample document splits into several sections and
    # retrieval becomes meaningful. In production the 512-token default is fine.
    settings = Settings(chunk_size=120, chunk_overlap=24, persist_vectorstore=False)
    container = build_container(settings)

    doc = load_file(SAMPLE)
    result = container.pipeline.ingest_documents([doc], collection="demo")
    print(f"Ingested {result.chunks} chunks from {doc.metadata['source']}\n")

    questions = [
        "What is retrieval-augmented generation and why does it reduce hallucinations?",
        "How does hybrid retrieval combine dense and sparse search?",
        "How do you evaluate the quality of a RAG system?",
    ]
    for q in questions:
        answer = container.rag_engine.answer(q, collection="demo", top_k=3)
        print("=" * 78)
        print(f"Q: {q}")
        print(f"A: {answer.answer}")
        print(f"   (llm={container.llm.name}, latency={answer.latency_ms} ms)")
        print("   sources:")
        for i, src in enumerate(answer.sources, start=1):
            preview = src.text[:70].replace("\n", " ")
            print(f"     [{i}] score={src.score:.4f} {src.metadata.get('source')} :: {preview}...")
        print()

    # Retrieval quality against a tiny labelled set.
    corpus = container.vectorstore.iter_corpus("demo")
    rag_ids = [c.id for c in corpus if "retrieval-augmented" in c.text.lower()]
    report = evaluate_retrieval(
        container.retriever,
        dataset=[{"query": "what is RAG", "relevant_ids": rag_ids}],
        collection="demo",
        k=3,
    )
    print("=" * 78)
    print(
        f"Retrieval eval  ->  hit_rate={report.hit_rate:.2f}  "
        f"mrr={report.mrr:.2f}  (n={report.n})"
    )


if __name__ == "__main__":
    main()
