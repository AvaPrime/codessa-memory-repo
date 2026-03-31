from __future__ import annotations

"""Text chunking for the Codessa Memory ingestion pipeline.

Two modes
---------
preserve_whitespace=False (default)
    Collapses all whitespace to single spaces before chunking. Fast and
    appropriate for plain prose such as chat exports and markdown summaries.

preserve_whitespace=True
    Preserves the original whitespace structure (indentation, newlines).
    Use this for source code, SQL, YAML, architecture diagrams, or any
    markdown document where indentation carries semantic meaning.

    In this mode the chunker attempts to break on paragraph / block
    boundaries (double-newline) first. When a block is larger than
    chunk_size it falls back to a character-level split with overlap,
    identical to the prose strategy but applied to the raw text.
"""


def _char_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Sliding window character split. Used for both modes."""
    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end == length:
            break
        start = end - overlap
    return chunks


def _structured_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Block-aware split that tries paragraph/section boundaries first.

    Algorithm:
    1. Split on double newline to get natural blocks.
    2. Accumulate blocks into a window until adding the next block would
       exceed chunk_size. When the window is full, emit it.
    3. The next window starts by re-including the last `overlap` characters
       of the previous window (suffix overlap).
    4. Any single block that exceeds chunk_size on its own is sub-chunked
       with the sliding-window character split.
    """
    raw_blocks = text.split("\n\n")
    blocks: list[str] = []
    for block in raw_blocks:
        stripped = block.strip()
        if not stripped:
            continue
        if len(stripped) > chunk_size:
            blocks.extend(_char_chunks(stripped, chunk_size, overlap))
        else:
            blocks.append(stripped)

    if not blocks:
        return []

    chunks: list[str] = []
    window: list[str] = []
    window_len = 0
    separator = "\n\n"

    for block in blocks:
        addition = (len(separator) if window else 0) + len(block)
        if window and window_len + addition > chunk_size:
            chunk_text_str = separator.join(window)
            chunks.append(chunk_text_str)
            tail = chunk_text_str[-overlap:] if overlap else ""
            window = [tail, block] if tail else [block]
            window_len = len(tail) + (len(separator) if tail else 0) + len(block)
        else:
            window.append(block)
            window_len += addition

    if window:
        chunks.append(separator.join(w for w in window if w))

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 120,
    preserve_whitespace: bool = False,
) -> list[str]:
    """Split *text* into overlapping chunks of at most *chunk_size* characters."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    if not text or not text.strip():
        return []

    if preserve_whitespace:
        return _structured_chunks(text, chunk_size, overlap)

    normalised = " ".join(text.split())
    if not normalised:
        return []
    return _char_chunks(normalised, chunk_size, overlap)
