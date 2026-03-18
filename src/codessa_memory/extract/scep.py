from __future__ import annotations

from typing import Any


def heuristic_extract(chunk: str) -> dict[str, Any]:
    lower = chunk.lower()
    tags: list[str] = []
    for candidate in ["memory", "agent", "langgraph", "mcp", "notion", "github", "supabase"]:
        if candidate in lower:
            tags.append(candidate)

    entry_type = "architecture" if any(k in lower for k in ["architecture", "design", "system"]) else "note"
    reusable = any(k in lower for k in ["pattern", "template", "framework", "reusable"])

    summary = chunk[:280] + ("..." if len(chunk) > 280 else "")
    return {
        "title": None,
        "summary": summary,
        "entry_type": entry_type,
        "tags": tags,
        "reusable": reusable,
        "components": [],
        "system_links": [],
        "decisions": [],
        "next_steps": [],
    }
