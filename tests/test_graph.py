from app.rag.graph import build_semantic_graph


def test_build_semantic_graph(container):
    graph = build_semantic_graph(
        container.vectorstore, container.embedder, collection="default", k=2, min_sim=0.0
    )
    ids = {n.id for n in graph.nodes}
    assert len(graph.nodes) == container.vectorstore.count("default")
    # Edges reference existing nodes and are undirected (no duplicate pair).
    seen = set()
    for edge in graph.edges:
        assert edge.source in ids and edge.target in ids
        key = frozenset({edge.source, edge.target})
        assert key not in seen
        seen.add(key)


def test_graph_endpoint(client):
    resp = client.get("/graph", params={"collection": "default", "k": 2, "min_sim": 0.0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["collection"] == "default"
    assert len(body["nodes"]) >= 1
    assert "degree" in body["nodes"][0]


def test_graph_empty_collection(client):
    resp = client.get("/graph", params={"collection": "nope"})
    assert resp.status_code == 200
    assert resp.json()["nodes"] == []
