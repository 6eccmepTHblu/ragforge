def test_query_stream_emits_sse_events(client):
    resp = client.post(
        "/query/stream",
        json={"question": "what is retrieval augmented generation", "collection": "default"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert "event: sources" in body
    assert "event: token" in body
    assert "event: done" in body


def test_mock_llm_streams_multiple_tokens(container):
    from app.llm import system, user

    tokens = list(
        container.llm.stream([system("s"), user("Context: hello world. Question: hi")])
    )
    assert len(tokens) > 1
    assert "".join(tokens).startswith("[mock-llm]")
