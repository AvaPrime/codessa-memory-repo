from __future__ import annotations

import hashlib
import math
from collections import Counter
from functools import lru_cache

import httpx

from codessa_memory.utils.config import settings


def _tokenize(text: str) -> list[str]:
    return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if token]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _stable_token_index(token: str, dimensions: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False) % dimensions


def _embed_text_hash(text: str, dimensions: int = 384) -> list[float]:
    tokens = _tokenize(text)
    counts = Counter(tokens)
    vector = [0.0] * dimensions
    if not counts:
        return vector
    for token, count in counts.items():
        idx = _stable_token_index(token, dimensions)
        vector[idx] += float(count)
    return _normalize(vector)


@lru_cache(maxsize=2)
def _load_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "sentence-transformers is not installed. Run: pip install '.[embeddings]'"
        ) from exc
    return SentenceTransformer(model_name)


def _embed_text_sentence_transformer(text: str) -> list[float]:
    model = _load_sentence_transformer(settings.embedding_model)
    vector = model.encode(text, normalize_embeddings=True)
    return [float(value) for value in vector.tolist()]


def _embed_text_openai_compatible(text: str) -> list[float]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")

    base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
    model_name = settings.embedding_model or "text-embedding-3-small"

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model_name, "input": text},
        )
        response.raise_for_status()
        payload = response.json()

    embedding = payload["data"][0]["embedding"]
    return _normalize([float(value) for value in embedding])


def embed_text_local(text: str, dimensions: int = 384) -> list[float]:
    provider = settings.embedding_provider.strip().lower()

    if provider in {"local", "sentence-transformers", "sentence_transformer"}:
        vector = _embed_text_sentence_transformer(text)
    elif provider in {"openai", "openai-compatible", "openai_compatible"}:
        vector = _embed_text_openai_compatible(text)
    elif provider in {"hash", "legacy-local", "legacy_local"}:
        vector = _embed_text_hash(text, dimensions=dimensions)
    else:
        raise ValueError(
            f"Unsupported embedding provider '{settings.embedding_provider}'. "
            "Use local, openai, or hash."
        )

    if len(vector) != dimensions:
        raise ValueError(
            "Embedding dimension mismatch: "
            f"provider '{settings.embedding_provider}' returned {len(vector)} dimensions, "
            f"but the current store/schema expects {dimensions}. "
            "Update the vector schema and stored data before switching models."
        )
    return vector


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have same length")
    return sum(x * y for x, y in zip(a, b))
