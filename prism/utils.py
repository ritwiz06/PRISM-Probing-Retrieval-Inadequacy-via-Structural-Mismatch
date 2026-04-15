from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

from prism.schemas import Document, Triple


def ensure_directories(paths: Iterable[str | Path]) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def write_json(path: str | Path, payload: object) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_jsonl_documents(path: str | Path, documents: list[Document]) -> None:
    lines = [json.dumps(asdict(document)) for document in documents]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_jsonl_documents(path: str | Path) -> list[Document]:
    rows = Path(path).read_text(encoding="utf-8").strip().splitlines()
    return [Document(**json.loads(row)) for row in rows if row.strip()]


def write_jsonl_triples(path: str | Path, triples: list[Triple]) -> None:
    lines = [json.dumps(asdict(triple)) for triple in triples]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_jsonl_triples(path: str | Path) -> list[Triple]:
    rows = Path(path).read_text(encoding="utf-8").strip().splitlines()
    return [Triple(**json.loads(row)) for row in rows if row.strip()]
