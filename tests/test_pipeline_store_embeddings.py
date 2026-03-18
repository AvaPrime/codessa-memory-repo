from __future__ import annotations

from uuid import UUID

import pytest

from codessa_memory.ingest.pipeline import IngestionPipeline
from codessa_memory.retrieval.service import RetrievalService
from codessa_memory.storage.embeddings import cosine_similarity, embed_text_local
from codessa_memory.storage.local_store import LocalStore


def test_embed_text_local_is_deterministic() -> None:
    v1 = embed_text_local("hello world")
    v2 = embed_text_local("hello world")
    assert v1 == v2
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)


def test_local_store_roundtrip_and_query(tmp_path) -> None:
    store = LocalStore(str(tmp_path))
    pipeline = IngestionPipeline(store, chunk_size=50, overlap=5)
    entries = pipeline.ingest_text("alpha beta gamma " * 30, source="manual", source_ref="x")
    assert entries

    svc = RetrievalService(store, default_top_k=3)
    response = svc.query("alpha beta", top_k=2, source="manual")
    assert response.query == "alpha beta"
    assert len(response.results) <= 2
    assert all(isinstance(r.entry_id, UUID) for r in response.results)
    assert all(r.source == "manual" for r in response.results)
