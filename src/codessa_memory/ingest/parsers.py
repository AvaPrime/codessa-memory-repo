from pathlib import Path


def read_text_file(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in {".md", ".txt", ".json", ".py", ".yaml", ".yml", ".sql"}:
        raise ValueError(f"Unsupported text file type: {suffix}")
    return file_path.read_text(encoding="utf-8")
