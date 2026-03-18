from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from codessa_memory.di.container import Container, Lifetime, Scope
from codessa_memory.ingest.pipeline import IngestionPipeline
from codessa_memory.limits.http import RateLimitMiddleware
from codessa_memory.limits.service import RateLimiter
from codessa_memory.retrieval.service import RetrievalService
from codessa_memory.storage.local_store import LocalStore
from codessa_memory.utils.config import Settings, settings
from codessa_memory.utils.models import QueryRequest, QueryResponse


class ScopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Any:
        request.state.scope = {}
        return await call_next(request)


def _get_scope(request: Request) -> Scope:
    scope = getattr(request.state, "scope", None)
    if not isinstance(scope, dict):
        scope = {}
        request.state.scope = scope
    return scope


def resolve(key: type[Any]) -> Callable[[Request, Scope], Any]:
    def _dep(request: Request, scope: Scope = Depends(_get_scope)) -> Any:
        container: Container = request.app.state.container
        return container.resolve(key, scope=scope)

    return _dep


class IngestRequest(BaseModel):
    text: str
    source: str = "manual"
    source_ref: str | None = None


def create_container(app_settings: Settings, overrides: Mapping[type[Any], Any] | None = None) -> Container:
    container = Container()
    container.register_instance(Settings, app_settings)

    def _store(_c: Container, _s: Scope) -> LocalStore:
        return LocalStore(app_settings.local_data_dir)

    container.register(LocalStore, _store, lifetime=Lifetime.SINGLETON)

    def _pipeline(c: Container, _s: Scope) -> IngestionPipeline:
        store = c.resolve(LocalStore)
        return IngestionPipeline(store, app_settings.default_chunk_size, app_settings.default_chunk_overlap)

    container.register(IngestionPipeline, _pipeline, lifetime=Lifetime.SINGLETON)

    def _retrieval(c: Container, _s: Scope) -> RetrievalService:
        store = c.resolve(LocalStore)
        return RetrievalService(store, app_settings.top_k)

    container.register(RetrievalService, _retrieval, lifetime=Lifetime.SINGLETON)

    container.register(
        RateLimiter,
        lambda _c, _s: RateLimiter(requests_per_minute=app_settings.rate_limit_requests_per_minute),
        lifetime=Lifetime.SINGLETON,
    )

    if overrides:
        container.apply_overrides(overrides)

    return container


def create_app(app_settings: Settings | None = None, overrides: Mapping[type[Any], Any] | None = None) -> FastAPI:
    app_settings = settings if app_settings is None else app_settings
    container = create_container(app_settings, overrides=overrides)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        app.state.container.validate()
        yield

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.state.container = container

    public_prefixes = ("/health", "/docs", "/openapi.json", "/redoc")
    app.add_middleware(ScopeMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        limiter=container.resolve(RateLimiter),
        enabled=app_settings.rate_limit_enabled,
        public_prefixes=public_prefixes,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ingest")
    def ingest(request: IngestRequest, pipeline: IngestionPipeline = Depends(resolve(IngestionPipeline))) -> dict[str, object]:
        entries = pipeline.ingest_text(request.text, source=request.source, source_ref=request.source_ref)
        return {"ingested": len(entries), "entry_ids": [str(entry.id) for entry in entries]}

    @app.post("/query", response_model=QueryResponse)
    def query(request: QueryRequest, svc: RetrievalService = Depends(resolve(RetrievalService))) -> QueryResponse:
        return svc.query(request.query, top_k=request.top_k, source=request.source)

    return app
