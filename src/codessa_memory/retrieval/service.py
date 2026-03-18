from __future__ import annotations

from codessa_memory.storage.embeddings import embed_text_local
from codessa_memory.utils.models import QueryResponse


class RetrievalService:
    def __init__(self, store, default_top_k: int = 5) -> None:
        self.store = store
        self.default_top_k = default_top_k

    def query(self, query: str, top_k: int | None = None, source: str | None = None) -> QueryResponse:
        query_embedding = embed_text_local(query)
        results = self.store.query(query_embedding, top_k=top_k or self.default_top_k, source=source)
        return QueryResponse(query=query, results=results)
