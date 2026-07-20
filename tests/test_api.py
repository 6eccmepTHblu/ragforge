def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "mock"
    assert body["vectorstore"] == "memory"


def test_ingest_and_query_flow(client):
    ingest = client.post(
        "/ingest/text",
        json={
            "text": "Vector databases store embeddings for semantic search.",
            "collection": "kb",
            "source": "note.md",
        },
    )
    assert ingest.status_code == 200
    assert ingest.json()["chunks"] >= 1

    search = client.post(
        "/search", json={"query": "semantic search", "collection": "kb"}
    )
    assert search.status_code == 200
    assert len(search.json()["results"]) >= 1

    query = client.post(
        "/query", json={"question": "how are embeddings stored?", "collection": "kb"}
    )
    assert query.status_code == 200
    payload = query.json()
    assert payload["answer"]
    assert payload["sources"]


def test_collections_listing(client):
    resp = client.get("/collections")
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()["collections"]}
    assert "default" in names


def test_eval_judge_endpoint(client):
    resp = client.post(
        "/eval/judge",
        json={
            "question": "what is RAG?",
            "answer": "RAG augments an LLM with retrieval.",
            "contexts": ["Retrieval-Augmented Generation adds a retriever to an LLM."],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["faithfulness"] <= 1.0
    assert 0.0 <= body["answer_relevancy"] <= 1.0
