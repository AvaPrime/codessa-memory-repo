from __future__ import annotations

from codessa_memory.extract.scep import heuristic_extract
from codessa_memory.ingest.chunker import chunk_text
from codessa_memory.storage.embeddings import embed_text_local
from codessa_memory.utils.models import ChronoSpiralLog, CodexEntry


class IngestionPipeline:
    def __init__(self, store, chunk_size: int = 900, overlap: int = 120) -> None:
        self.store = store
        self.chunk_size = chunk_size
        self.overlap = overlap

    def ingest_text(self, text: str, source: str = "manual", source_ref: str | None = None) -> list[CodexEntry]:
        chunks = chunk_text(text, self.chunk_size, self.overlap)
        entries: list[CodexEntry] = []
        for chunk in chunks:
            extracted = heuristic_extract(chunk)
            entry = CodexEntry(
                title=extracted["title"],
                content=chunk,
                entry_type=extracted["entry_type"],
                source=source,
                source_ref=source_ref,
                tags=extracted["tags"],
                reusable=extracted["reusable"],
                metadata={
                    "summary": extracted["summary"],
                    "components": extracted["components"],
                    "system_links": extracted["system_links"],
                },
            )
            embedding = embed_text_local(chunk)
            self.store.save_entry(entry, embedding)
            entries.append(entry)

        if entries:
            log = ChronoSpiralLog(
                session_label=f"ingest:{source}",
                summary=f"Ingested {len(entries)} entries from {source}",
                decisions=["Chunked source content", "Stored entries with embeddings"],
                next_steps=["Run retrieval validation", "Promote reusable entries"],
                linked_entries=[entry.id for entry in entries],
            )
            self.store.save_log(log)
        return entries
