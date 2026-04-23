from __future__ import annotations

from pathlib import Path

from prism.open_corpus.normalize_documents import NormalizedDocument, normalize_file

SUPPORTED_SUFFIXES = {".txt", ".md", ".html", ".htm", ".json"}


def load_local_documents(paths: list[str | Path]) -> list[NormalizedDocument]:
    files: list[Path] = []
    for path in paths:
        current = Path(path)
        if current.is_dir():
            files.extend(sorted(file for file in current.rglob("*") if file.is_file() and file.suffix.lower() in SUPPORTED_SUFFIXES))
        elif current.is_file() and current.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(current)
    return [normalize_file(file) for file in files]

