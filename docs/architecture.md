# Architecture & design notes

This document explains *why* RAGForge is built the way it is. The guiding
principle: keep every external dependency (LLM, embedding model, vector DB)
behind a narrow interface so the core logic stays testable and vendor-neutral.

## Layers

```
API (FastAPI routers)
        │  depends on
        ▼
Dependencies (Container)  ── wires the object graph once
        │
        ▼
RAG engine ── retrieval ── vector store
        │         │
        ▼         ▼
   LLM provider   embedder
        │
        ▼
   Evaluation (metrics + judge)
```

Each arrow is a dependency on an **interface**, not a concrete class. The
`Container` (see `app/dependencies.py`) is the single place where concrete
implementations are selected from `Settings`.

## Key decisions

### 1. An offline-first default path

The default configuration (`mock` LLM, `hash` embeddings, `memory` store) has no
network calls and no secrets. This is deliberate:

- **CI can run the full pipeline** — ingestion, hybrid retrieval, generation and
  evaluation — deterministically.
- **Reviewers can try it in 30 seconds** without provisioning API keys.
- It forces the abstractions to be honest: if the mock backends couldn't satisfy
  the interface, the interface would be leaking vendor details.

The `HashEmbedder` uses the hashing trick over word tokens and character
tri-grams. It is *lexical*, not neural — good enough to exercise retrieval
ordering deterministically, and clearly documented as a dev/test stand-in.

### 2. Hybrid retrieval with Reciprocal Rank Fusion

Dense embeddings capture meaning but can miss exact tokens (IDs, rare names);
BM25 captures exact tokens but ignores semantics. We run both and fuse them.

RRF (`1 / (k + rank)`, summed across lists) is used instead of a weighted score
sum because cosine similarities and BM25 scores are on different, non-comparable
scales — fusing on **rank** sidesteps that entirely. The BM25 index is cached per
collection and rebuilt only when the collection size changes.

### 3. Token-aware recursive chunking

`TextSplitter` (in `app/core/chunking.py`) is implemented from scratch rather
than imported, so the behaviour is explicit and unit-tested. It recursively
tries coarser-to-finer separators (paragraph → line → sentence → word →
character), measuring length in **tokens** (via `tiktoken`, with a whitespace
fallback), and carries `chunk_overlap` tokens between neighbours to preserve
context across boundaries.

### 4. Evaluation in the box

- **Retrieval metrics** (`hit_rate@k`, `MRR@k`) score the retriever alone against
  a labelled set — cheap, deterministic, ideal for regression tests.
- **LLM-as-judge** scores generated answers for *faithfulness* (grounded in the
  context?) and *answer relevancy* (addresses the question?). The judge is just
  another use of the `LLMProvider` interface, so the mock backend can stand in
  during tests.

### 5. Streaming

`/query/stream` emits Server-Sent Events: first a `sources` event (so the UI can
render citations immediately), then `token` events as the LLM generates, then
`done`. Providers implement `stream()`; the base class falls back to yielding the
full response once, so non-streaming backends still work through the same path.

## Extending

- **New vector store:** implement `VectorStore` (`add`, `search`, `count`,
  `list_collections`, `delete_collection`, and optionally `iter_corpus` to enable
  hybrid search) and register it in `vectorstore/factory.py`.
- **New LLM/embedding provider:** implement the interface and register it in the
  corresponding factory. Nothing else changes.

## Known limitations (honest list)

- The in-memory store does exact (brute-force) cosine search — great up to tens
  of thousands of chunks, not a billion-vector ANN index. Use Chroma/Qdrant for
  scale.
- Hybrid search rebuilds BM25 from the full corpus when the collection grows;
  fine for moderate corpora, would want an incremental index at large scale.
- LLM/embedding calls are synchronous; batching and async are on the roadmap.
