from __future__ import annotations

from codessa_memory.extract.scep import heuristic_extract


def test_heuristic_extract_tags_and_flags() -> None:
    chunk = "Architecture for MCP memory system. Reusable pattern for Supabase."
    extracted = heuristic_extract(chunk)
    assert extracted["entry_type"] == "architecture"
    assert extracted["reusable"] is True
    assert "mcp" in extracted["tags"]
    assert "supabase" in extracted["tags"]
