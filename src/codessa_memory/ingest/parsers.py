from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TEXT_EXTENSIONS = {".md", ".txt", ".json", ".py", ".yaml", ".yml", ".sql"}


def _stringify_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            text = _stringify_content(item)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"].strip()
        if isinstance(value.get("content"), str):
            return value["content"].strip()
        if isinstance(value.get("parts"), list):
            return _stringify_content(value["parts"])
        if value.get("type") == "text" and isinstance(value.get("text"), str):
            return value["text"].strip()
    return ""


def _render_messages(messages: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for message in messages:
        role = str(message.get("role") or message.get("speaker") or "unknown").strip().lower()
        content = _stringify_content(message.get("content"))
        if not content and "parts" in message:
            content = _stringify_content(message.get("parts"))
        if not content:
            continue
        rendered.append(f"{role}: {content}")
    return "\n\n".join(rendered).strip()


def _parse_chatgpt_mapping(payload: dict[str, Any]) -> str:
    mapping = payload.get("mapping")
    if not isinstance(mapping, dict):
        return ""

    rows: list[tuple[float, str, str]] = []
    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author") or {}
        role = str(author.get("role") or "unknown").strip().lower()

        content_obj = message.get("content") or {}
        if isinstance(content_obj, dict):
            content = _stringify_content(content_obj.get("parts") or content_obj.get("text") or content_obj)
        else:
            content = _stringify_content(content_obj)
        if not content:
            continue

        created = node.get("create_time") or message.get("create_time") or 0.0
        try:
            sort_key = float(created)
        except (TypeError, ValueError):
            sort_key = 0.0
        rows.append((sort_key, role, content))

    rows.sort(key=lambda item: item[0])
    return "\n\n".join(f"{role}: {content}" for _, role, content in rows).strip()


def parse_chat_export(path: str) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if isinstance(payload, list):
        if payload and all(isinstance(item, dict) and "role" in item for item in payload):
            return _render_messages(payload)

        conversations: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Untitled conversation").strip()
            body = ""
            if isinstance(item.get("messages"), list):
                body = _render_messages(item["messages"])
            elif isinstance(item.get("mapping"), dict):
                body = _parse_chatgpt_mapping(item)
            if body:
                conversations.append(f"# {title}\n\n{body}")
        if conversations:
            return "\n\n---\n\n".join(conversations)

    if isinstance(payload, dict):
        if isinstance(payload.get("messages"), list):
            return _render_messages(payload["messages"])
        if isinstance(payload.get("mapping"), dict):
            return _parse_chatgpt_mapping(payload)

    raise ValueError("JSON file is not a supported Claude or ChatGPT export format")


def read_text_file(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported text file type: {suffix}")

    if suffix == ".json":
        try:
            return parse_chat_export(path)
        except ValueError:
            return file_path.read_text(encoding="utf-8")

    return file_path.read_text(encoding="utf-8")
