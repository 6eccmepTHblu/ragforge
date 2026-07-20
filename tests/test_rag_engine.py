def test_answer_is_grounded_and_has_sources(container):
    result = container.rag_engine.answer(
        "what is retrieval augmented generation", collection="default", top_k=3
    )
    assert result.answer
    assert result.sources
    assert result.latency_ms >= 0
    # The mock LLM grounds its answer in the retrieved context.
    assert "retrieval" in result.answer.lower() or "context" in result.answer.lower()


def test_answer_on_empty_collection(container):
    result = container.rag_engine.answer(
        "anything", collection="does-not-exist", top_k=3
    )
    assert result.sources == []
    assert result.answer  # mock still returns a (no-context) message
