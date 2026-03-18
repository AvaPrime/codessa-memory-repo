from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CodexEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str | None = None
    content: str
    entry_type: str = "note"
    source: str = "manual"
    source_ref: str | None = None
    tags: list[str] = Field(default_factory=list)
    reusable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChronoSpiralLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_label: str | None = None
    summary: str
    decisions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    linked_entries: list[UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None
    source: str | None = None


class QueryResult(BaseModel):
    entry_id: UUID
    title: str | None = None
    content: str
    source: str
    similarity: float


class QueryResponse(BaseModel):
    query: str
    results: list[QueryResult]
