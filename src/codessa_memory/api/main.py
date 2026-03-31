from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from codessa_memory.ingest.pipeline import IngestionPipeline
from codessa_memory.retrieval.service import RetrievalService
from codessa_memory.storage.local_store import LocalStore
from codessa_memory.utils.config import settings
from codessa_memory.utils.models import QueryRequest, QueryResponse

app = FastAPI(title=settings.app_name)

_backend = settings.storage_backend.strip().lower()
if _backend in {"postgres", "supabase"}:
    from codessa_memory.storage.supabase_store import SupabaseStore

    if not settings.postgres_dsn:
        raise RuntimeError(
            "STORAGE_BACKEND=postgres requires POSTGRES_DSN to be set in .env"
        )
    store: Any = SupabaseStore(dsn=settings.postgres_dsn)
else:
    store = LocalStore(settings.local_data_dir)

ingestion_pipeline = IngestionPipeline(store, settings.default_chunk_size, settings.default_chunk_overlap)
retrieval_service = RetrievalService(store, settings.top_k)


class IngestRequest(BaseModel):
    text: str
    source: str = "manual"
    source_ref: str | None = None
    preserve_whitespace: bool = False


@app.get("/health")
def health() -> dict[str, Any]:
    base: dict[str, Any] = {"status": "ok", "storage_backend": _backend}
    if hasattr(store, "health_check"):
        base.update(store.health_check())
    return base


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, object]:
    entries = ingestion_pipeline.ingest_text(
        request.text,
        source=request.source,
        source_ref=request.source_ref,
        preserve_whitespace=request.preserve_whitespace,
    )
    return {"ingested": len(entries), "entry_ids": [str(entry.id) for entry in entries]}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return retrieval_service.query(request.query, top_k=request.top_k, source=request.source)
