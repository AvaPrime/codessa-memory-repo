from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from codessa_memory.ingest.pipeline import IngestionPipeline
from codessa_memory.retrieval.service import RetrievalService
from codessa_memory.storage.local_store import LocalStore
from codessa_memory.utils.config import settings
from codessa_memory.utils.models import QueryRequest, QueryResponse

app = FastAPI(title=settings.app_name)
store = LocalStore(settings.local_data_dir)
ingestion_pipeline = IngestionPipeline(store, settings.default_chunk_size, settings.default_chunk_overlap)
retrieval_service = RetrievalService(store, settings.top_k)


class IngestRequest(BaseModel):
    text: str
    source: str = "manual"
    source_ref: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, object]:
    entries = ingestion_pipeline.ingest_text(request.text, source=request.source, source_ref=request.source_ref)
    return {"ingested": len(entries), "entry_ids": [str(entry.id) for entry in entries]}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return retrieval_service.query(request.query, top_k=request.top_k, source=request.source)
