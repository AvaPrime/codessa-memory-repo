# Codessa Memory
A production-oriented starter repository for the **Codessa Memory Layer (CML)**.

It provides:
- document and chat ingestion
- structured Codex extraction
- vector + metadata storage via Supabase/Postgres
- local development mode via SQLite/JSONL
- retrieval pipeline scaffold
- FastAPI service for ingest and query
- Docker Compose stack for local orchestration

## Architecture

```text
inputs -> parsing -> chunking -> SCEP extraction -> embeddings -> storage -> retrieval -> ChronoSpiral logs
```

## Repo layout

```text
codessa-memory-repo/
  src/codessa_memory/
    api/               FastAPI app
    extract/           SCEP/Codex extraction logic
    ingest/            parsers, chunking, pipeline
    retrieval/         query pipeline
    storage/           Supabase and local stores
    utils/             shared config and helpers
  prompts/             system and extraction prompts
  sql/                 schema and indexes
  tests/               basic tests
  scripts/             setup and bootstrap scripts
  docs/                implementation docs
  config/              example configuration files
```

## Quick start

### 1) Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2) Configure environment

```bash
cp .env.example .env
```

Fill in the variables for your preferred embedding provider and database.

### 3) Run local API

```bash
uvicorn codessa_memory.api.main:app --reload
```

### 4) Ingest a file

```bash
python scripts/ingest_file.py path/to/file.md --source manual
```

### 5) Query memory

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What did we decide about the checkpoint store?"}'
```

## Modes

### Production
- Supabase/Postgres for structured memory
- pgvector for embeddings
- OpenAI-compatible embeddings

### Local development
- JSONL storage for entries and ChronoSpiral logs
- in-memory cosine similarity fallback

## Next upgrades
- GitHub repo ingestion
- Notion sync worker
- Google Drive connector ingestion
- LangGraph memory router
- MCP retrieval server

## License

Internal / private by default.
