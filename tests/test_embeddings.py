import numpy as np

from app.embeddings.hash_embedder import HashEmbedder


def _cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def test_dimension_and_determinism():
    emb = HashEmbedder(dimension=256)
    v1 = emb.embed_query("machine learning models")
    v2 = emb.embed_query("machine learning models")
    assert len(v1) == 256
    assert v1 == v2  # deterministic across calls


def test_similar_text_scores_higher_than_dissimilar():
    emb = HashEmbedder(dimension=512)
    anchor = emb.embed_query("neural networks for natural language processing")
    similar = emb.embed_query("neural networks and natural language models")
    different = emb.embed_query("a recipe for baking chocolate cake")
    assert _cosine(anchor, similar) > _cosine(anchor, different)


def test_batch_matches_single():
    emb = HashEmbedder(dimension=128)
    batch = emb.embed_documents(["alpha", "beta"])
    assert batch[0] == emb.embed_query("alpha")
    assert batch[1] == emb.embed_query("beta")
