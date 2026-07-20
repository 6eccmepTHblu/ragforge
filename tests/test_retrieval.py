from app.retrieval.bm25 import BM25Index
from app.retrieval.hybrid import reciprocal_rank_fusion


def test_bm25_ranks_keyword_match_first():
    docs = [
        "docker packages applications into container images",
        "fastapi is a python web framework",
        "retrieval augmented generation uses embeddings",
    ]
    index = BM25Index().build(docs)
    hits = index.search("python web framework", top_k=3)
    assert hits[0][0] == 1  # the FastAPI doc


def test_bm25_returns_nothing_for_unknown_terms():
    index = BM25Index().build(["alpha beta gamma"])
    assert index.search("zzz qqq", top_k=3) == []


def test_reciprocal_rank_fusion_rewards_agreement():
    dense = ["x", "y", "z"]
    sparse = ["y", "x", "w"]
    fused = reciprocal_rank_fusion([dense, sparse], k=60)
    # "y" is 2nd in dense but 1st in sparse; "x" is 1st in dense but 2nd in sparse.
    assert set(fused) == {"x", "y", "z", "w"}
    assert fused["x"] > fused["z"]
    assert fused["y"] > fused["w"]


def test_hybrid_retriever_finds_relevant_chunk(container):
    results = container.retriever.retrieve(
        "what is retrieval augmented generation", collection="default", top_k=3
    )
    assert results
    top_sources = {r.metadata.get("source") for r in results[:2]}
    assert "rag.md" in top_sources


def test_dense_only_when_hybrid_disabled(container):
    container.settings.use_hybrid = False
    results = container.retriever.retrieve(
        "docker container images", collection="default", top_k=2
    )
    assert results
