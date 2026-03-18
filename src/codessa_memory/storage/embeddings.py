from __future__ import annotations

import hashlib
import math
from collections import Counter


def _tokenize(text: str) -> list[str]:
    return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token]


def _stable_token_index(token: str, dimensions: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False) % dimensions


def embed_text_local(text: str, dimensions: int = 384) -> list[float]:
    tokens = _tokenize(text)
    counts = Counter(tokens)
    vector = [0.0] * dimensions
    if not counts:
        return vector
    for token, count in counts.items():
        idx = _stable_token_index(token, dimensions)
        vector[idx] += float(count)
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have same length")
    return sum(x * y for x, y in zip(a, b))
