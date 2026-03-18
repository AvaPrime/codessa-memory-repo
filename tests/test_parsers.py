from __future__ import annotations

import pytest

from codessa_memory.ingest.parsers import read_text_file


def test_read_text_file_reads_supported_suffix(tmp_path) -> None:
    p = tmp_path / "x.md"
    p.write_text("hello", encoding="utf-8")
    assert read_text_file(str(p)) == "hello"


def test_read_text_file_rejects_unsupported_suffix(tmp_path) -> None:
    p = tmp_path / "x.bin"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        read_text_file(str(p))
