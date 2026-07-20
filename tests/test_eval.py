from app.eval.metrics import evaluate_retrieval, hit_rate_at_k, mrr_at_k


def test_hit_rate_and_mrr():
    assert hit_rate_at_k(["a", "b", "c"], {"c"}) == 1.0
    assert hit_rate_at_k(["a", "b"], {"z"}) == 0.0
    assert mrr_at_k(["a", "b", "c"], {"b"}) == 0.5
    assert mrr_at_k(["a", "b"], {"z"}) == 0.0


def test_evaluate_retrieval_runs(container):
    # Pull a real chunk id from the RAG document to use as ground truth.
    corpus = container.vectorstore.iter_corpus("default")
    rag_ids = [c.id for c in corpus if c.metadata.get("source") == "rag.md"]
    dataset = [
        {"query": "retrieval augmented generation embeddings", "relevant_ids": rag_ids}
    ]
    report = evaluate_retrieval(container.retriever, dataset, collection="default", k=3)
    assert report.n == 1
    assert 0.0 <= report.hit_rate <= 1.0
    assert report.hit_rate == 1.0  # the relevant chunk should be retrieved


def test_judge_returns_scores(container):
    result = container.judge.evaluate(
        question="what is RAG?",
        answer="RAG combines retrieval with generation.",
        contexts=["Retrieval-Augmented Generation combines a retriever with an LLM."],
    )
    assert 0.0 <= result.faithfulness <= 1.0
    assert 0.0 <= result.answer_relevancy <= 1.0
    assert result.reasoning
