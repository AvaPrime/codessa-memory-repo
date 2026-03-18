#!/usr/bin/env python3
from __future__ import annotations

import argparse

from codessa_memory.ingest.parsers import read_text_file
from codessa_memory.ingest.pipeline import IngestionPipeline
from codessa_memory.storage.local_store import LocalStore
from codessa_memory.utils.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a local text file into Codessa Memory")
    parser.add_argument("path")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--source-ref", default=None)
    args = parser.parse_args()

    text = read_text_file(args.path)
    store = LocalStore(settings.local_data_dir)
    pipeline = IngestionPipeline(store, settings.default_chunk_size, settings.default_chunk_overlap)
    entries = pipeline.ingest_text(text, source=args.source, source_ref=args.source_ref)
    print(f"Ingested {len(entries)} entries")


if __name__ == "__main__":
    main()
