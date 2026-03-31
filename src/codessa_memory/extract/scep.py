from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from codessa_memory.utils.config import settings

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "codex_extraction_prompt.md"
DEFAULT_LLM_MODEL = os.getenv("CODEX_EXTRACTION_MODEL", "gpt-4.1-mini")
DEFAULT_PROVIDER = os.getenv("CODEX_EXTRACTION_PROVIDER", "").strip().lower()
DEFAULT_TIMEOUT_S = float(os.getenv("CODEX_EXTRACTION_TIMEOUT_S", "30"))


def _load_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8").strip()
    return (
        "Analyze the content and return JSON with keys: "
        "title, summary, entry_type, tags, reusable, components, system_links, decisions, next_steps."
    )


def _short_title_from_chunk(chunk: str, limit: int = 96) -> str | None:
    for line in chunk.splitlines():
        candidate = line.strip().lstrip("#-*0123456789. ")
        if candidate:
            return candidate[:limit]
    return None


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                result.append(text)
        return result
    text = str(value).strip()
    return [text] if text else []


def _sanitize_extraction(chunk: str, payload: dict[str, Any]) -> dict[str, Any]:
    summary = str(payload.get("summary") or chunk[:280]).strip()
    if len(summary) > 280:
        summary = summary[:277] + "..."

    entry_type = str(payload.get("entry_type") or "note").strip().lower() or "note"
    allowed_entry_types = {
        "architecture",
        "system",
        "strategy",
        "decision",
        "implementation",
        "code",
        "research",
        "note",
    }
    if entry_type not in allowed_entry_types:
        entry_type = "note"

    title = payload.get("title")
    title = str(title).strip() if title else _short_title_from_chunk(chunk)

    return {
        "title": title or None,
        "summary": summary,
        "entry_type": entry_type,
        "tags": _as_str_list(payload.get("tags")),
        "reusable": bool(payload.get("reusable", False)),
        "components": _as_str_list(payload.get("components")),
        "system_links": _as_str_list(payload.get("system_links")),
        "decisions": _as_str_list(payload.get("decisions")),
        "next_steps": _as_str_list(payload.get("next_steps")),
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in extraction response")
    return json.loads(text[start : end + 1])


def _call_openai_compatible_extractor(chunk: str) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        return None

    base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
    provider = DEFAULT_PROVIDER or "openai"
    if provider not in {"openai", "openai-compatible", "openai_compatible"}:
        return None

    system_prompt = _load_prompt()
    user_prompt = f"Content:\n\n{chunk}"

    with httpx.Client(timeout=DEFAULT_TIMEOUT_S) as client:
        response = client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEFAULT_LLM_MODEL,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()

    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        content = "\n".join(text_parts)

    if not isinstance(content, str):
        raise ValueError("Unexpected extraction response format")
    return _sanitize_extraction(chunk, _extract_json_object(content))


def _heuristic_extract(chunk: str) -> dict[str, Any]:
    lower = chunk.lower()

    tags: list[str] = []
    components: list[str] = []
    system_links: list[str] = []

    keyword_map = {
        "memory": "memory",
        "agent": "agent",
        "langgraph": "langgraph",
        "mcp": "mcp",
        "notion": "notion",
        "github": "github",
        "supabase": "supabase",
        "postgres": "postgres",
        "pgvector": "pgvector",
        "chronospiral": "chronospiral",
        "ecl": "ecl",
    }
    for needle, tag in keyword_map.items():
        if needle in lower:
            tags.append(tag)

    component_map = {
        "api": "api",
        "pipeline": "pipeline",
        "parser": "parser",
        "retrieval": "retrieval",
        "embedding": "embeddings",
        "vector": "vector-store",
        "store": "storage",
        "chronospiral": "chronospiral",
    }
    for needle, component in component_map.items():
        if needle in lower:
            components.append(component)

    system_map = {
        "codessa": "Codessa OS",
        "memory cortex": "Memory Cortex",
        "mission control": "Mission Control",
        "chronospiral": "ChronoSpiral",
        "ecl": "Epistemic Confidence Layer",
        "mcl": "Meta Cognition Layer",
    }
    for needle, system_name in system_map.items():
        if needle in lower:
            system_links.append(system_name)

    if any(token in lower for token in ["architecture", "design", "system"]):
        entry_type = "architecture"
    elif any(token in lower for token in ["decision", "decide", "tradeoff"]):
        entry_type = "decision"
    elif any(token in lower for token in ["implement", "function", "class", "api", "endpoint", "sql"]):
        entry_type = "implementation"
    else:
        entry_type = "note"

    reusable = any(token in lower for token in ["pattern", "template", "framework", "reusable"])
    summary = chunk[:280] + ("..." if len(chunk) > 280 else "")

    decisions = [
        line.strip("- *")
        for line in chunk.splitlines()
        if line.strip().lower().startswith(("decision", "decided", "we will", "choose "))
    ]
    next_steps = [
        line.strip("- *")
        for line in chunk.splitlines()
        if line.strip().lower().startswith(("next", "todo", "action", "follow-up"))
    ]

    return {
        "title": _short_title_from_chunk(chunk),
        "summary": summary,
        "entry_type": entry_type,
        "tags": sorted(set(tags)),
        "reusable": reusable,
        "components": sorted(set(components)),
        "system_links": sorted(set(system_links)),
        "decisions": decisions,
        "next_steps": next_steps,
    }


def heuristic_extract(chunk: str) -> dict[str, Any]:
    """Public extraction entrypoint.

    If a compatible LLM is configured, use structured extraction first.
    Otherwise fall back to deterministic heuristics.
    """
    try:
        extracted = _call_openai_compatible_extractor(chunk)
        if extracted is not None:
            return extracted
    except Exception:
        pass
    return _heuristic_extract(chunk)
