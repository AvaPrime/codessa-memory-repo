from codessa_memory.ingest.chunker import chunk_text


def test_chunk_text_returns_chunks() -> None:
    text = "abc " * 500
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks
    assert all(len(chunk) <= 100 for chunk in chunks)
