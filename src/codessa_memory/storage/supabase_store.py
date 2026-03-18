from __future__ import annotations

from typing import Any

from codessa_memory.utils.models import ChronoSpiralLog, CodexEntry, QueryResult


class SupabaseStore:
    """Minimal placeholder for production integration.

    Replace internals with your preferred Supabase or direct Postgres client.
    """

    def __init__(self, url: str, service_role_key: str) -> None:
        self.url = url
        self.service_role_key = service_role_key

    def save_entry(self, entry: CodexEntry, embedding: list[float]) -> None:
        raise NotImplementedError("Implement Supabase insert logic for codex_entries and codex_embeddings")

    def save_log(self, log: ChronoSpiralLog) -> None:
        raise NotImplementedError("Implement Supabase insert logic for chronospiral_logs")

    def query(self, query_embedding: list[float], top_k: int = 5, source: str | None = None) -> list[QueryResult]:
        raise NotImplementedError("Implement RPC call to match_codex_entries")
