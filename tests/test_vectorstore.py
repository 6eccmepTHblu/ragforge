import os

from app.vectorstore.base import VectorRecord
from app.vectorstore.memory_store import MemoryVectorStore


def _records():
    return [
        VectorRecord(id="a", text="cat", embedding=[1.0, 0.0, 0.0], metadata={"s": "1"}),
        VectorRecord(id="b", text="dog", embedding=[0.0, 1.0, 0.0], metadata={"s": "2"}),
        VectorRecord(id="c", text="fish", embedding=[0.9, 0.1, 0.0], metadata={"s": "3"}),
    ]


def test_search_orders_by_cosine():
    store = MemoryVectorStore()
    store.add(_records(), collection="default")
    hits = store.search([1.0, 0.0, 0.0], top_k=2, collection="default")
    assert [h.id for h in hits] == ["a", "c"]
    assert hits[0].score >= hits[1].score


def test_count_list_delete():
    store = MemoryVectorStore()
    store.add(_records(), collection="default")
    assert store.count("default") == 3
    assert store.list_collections() == ["default"]
    store.delete_collection("default")
    assert store.count("default") == 0


def test_persistence_roundtrip(tmp_path):
    path = os.path.join(tmp_path, "store.json")
    store = MemoryVectorStore(persist_path=path)
    store.add(_records(), collection="default")
    assert os.path.exists(path)

    reloaded = MemoryVectorStore(persist_path=path)
    assert reloaded.count("default") == 3
    hits = reloaded.search([1.0, 0.0, 0.0], top_k=1, collection="default")
    assert hits[0].id == "a"


def test_iter_corpus():
    store = MemoryVectorStore()
    store.add(_records(), collection="default")
    corpus = store.iter_corpus("default")
    assert {c.id for c in corpus} == {"a", "b", "c"}
