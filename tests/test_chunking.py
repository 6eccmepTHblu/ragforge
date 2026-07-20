from app.core.chunking import TextSplitter, token_length


def test_small_text_single_chunk():
    splitter = TextSplitter(chunk_size=128, chunk_overlap=16)
    chunks = splitter.split("A short sentence about AI.")
    assert chunks == ["A short sentence about AI."]


def test_chunks_respect_size():
    text = ". ".join(f"Sentence number {i} about machine learning" for i in range(200))
    splitter = TextSplitter(chunk_size=64, chunk_overlap=8)
    chunks = splitter.split(text)
    assert len(chunks) > 1
    for chunk in chunks:
        # Allow a small slack because a single indivisible token run can exist.
        assert token_length(chunk) <= 80


def test_no_empty_chunks():
    text = "Para one.\n\n\n\nPara two.\n\n   \n\nPara three."
    splitter = TextSplitter(chunk_size=32, chunk_overlap=4)
    chunks = splitter.split(text)
    assert all(c.strip() for c in chunks)


def test_overlap_must_be_smaller_than_size():
    import pytest

    with pytest.raises(ValueError):
        TextSplitter(chunk_size=64, chunk_overlap=64)
