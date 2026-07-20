def test_memory_store_delete_by_id(container):
    store = container.vectorstore
    corpus = store.iter_corpus("default")
    victim = corpus[0].id
    before = store.count("default")
    removed = store.delete([victim], collection="default")
    assert removed == 1
    assert store.count("default") == before - 1
    assert victim not in {c.id for c in store.iter_corpus("default")}


def test_delete_missing_id_is_noop(container):
    assert container.vectorstore.delete(["does-not-exist"], collection="default") == 0


def test_list_documents_endpoint(client):
    resp = client.get("/documents", params={"collection": "default"})
    assert resp.status_code == 200
    sources = {d["source"] for d in resp.json()["documents"]}
    assert {"rag.md", "fastapi.md", "docker.md"} <= sources


def test_delete_document_endpoint(client):
    # docker.md was ingested as a single chunk in the fixture.
    resp = client.delete("/documents", params={"collection": "default", "source": "docker.md"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] >= 1
    remaining = client.get("/documents", params={"collection": "default"}).json()
    assert "docker.md" not in {d["source"] for d in remaining["documents"]}


def test_delete_chunk_endpoint(client):
    graph = client.get("/graph", params={"collection": "default"}).json()
    chunk_id = graph["nodes"][0]["id"]
    resp = client.delete(f"/chunks/{chunk_id}", params={"collection": "default"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1


def test_delete_updates_retrieval(container):
    # Deleting a source removes it from subsequent hybrid retrieval.
    ids = [c.id for c in container.vectorstore.iter_corpus("default")
           if c.metadata.get("source") == "docker.md"]
    container.vectorstore.delete(ids, collection="default")
    results = container.retriever.retrieve("docker containers", collection="default", top_k=5)
    assert "docker.md" not in {r.metadata.get("source") for r in results}
