from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from codessa_memory.storage.embeddings import cosine_similarity
from codessa_memory.utils.models import ChronoSpiralLog, CodexEntry, QueryResult


class LocalStore:
    def __init__(self, root_dir: str) -> None:
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.entries_file = self.root / "entries.jsonl"
        self.logs_file = self.root / "chronospiral.jsonl"

    def save_entry(self, entry: CodexEntry, embedding: list[float]) -> None:
        row = entry.model_dump(mode="json")
        row["embedding"] = embedding
        with self.entries_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    def save_log(self, log: ChronoSpiralLog) -> None:
        with self.logs_file.open("a", encoding="utf-8") as fh:
            fh.write(log.model_dump_json() + "\n")

    def query(self, query_embedding: list[float], top_k: int = 5, source: str | None = None) -> list[QueryResult]:
        if not self.entries_file.exists():
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for line in self.entries_file.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if source and row.get("source") != source:
                continue
            sim = cosine_similarity(query_embedding, row["embedding"])
            scored.append((sim, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[QueryResult] = []
        for sim, row in scored[:top_k]:
            results.append(
                QueryResult(
                    entry_id=UUID(row["id"]),
                    title=row.get("title"),
                    content=row["content"],
                    source=row["source"],
                    similarity=sim,
                )
            )
        return results
