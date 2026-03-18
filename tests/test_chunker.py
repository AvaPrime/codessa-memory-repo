import pytest

from codessa_memory.ingest.chunker import chunk_text


def test_chunk_text_returns_chunks() -> None:
    text = "abc " * 500
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_chunk_text_empty_returns_empty() -> None:
    assert chunk_text("   \n\t  ", chunk_size=10, overlap=1) == []


def test_chunk_text_validates_inputs() -> None:
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        chunk_text("x" * 20, chunk_size=10, overlap=10)
