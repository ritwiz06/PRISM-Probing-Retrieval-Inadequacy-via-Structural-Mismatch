from __future__ import annotations

from pathlib import Path

from prism.open_corpus.build_source_pack import build_source_pack
from prism.open_corpus.load_local_docs import load_local_documents
from prism.open_corpus.normalize_documents import document_metadata_payload
from prism.schemas import Document
from prism.utils import read_jsonl_documents, write_json, write_jsonl_documents

RUNTIME_ROOT = Path("data/runtime_corpora")


def build_runtime_corpus_from_local(paths: list[str | Path], name: str = "local_demo") -> dict[str, object]:
    normalized = load_local_documents(paths)
    output_dir = RUNTIME_ROOT / name
    output_dir.mkdir(parents=True, exist_ok=True)
    documents_path = output_dir / "documents.jsonl"
    metadata_path = output_dir / "metadata.json"
    write_jsonl_documents(documents_path, [entry.document for entry in normalized])
    metadata = document_metadata_payload(name, normalized)
    metadata.update({"output_dir": str(output_dir), "documents_path": str(documents_path), "mode": "local_folder"})
    write_json(metadata_path, metadata)
    return {
        "name": name,
        "document_count": len(normalized),
        "output_dir": str(output_dir),
        "documents_path": str(documents_path),
        "metadata_path": str(metadata_path),
    }


def load_runtime_documents(output_dir: str | Path) -> list[Document]:
    return read_jsonl_documents(Path(output_dir) / "documents.jsonl")


def ensure_source_pack_documents(pack: str) -> tuple[dict[str, object], list[Document]]:
    summary = build_source_pack(pack)
    return summary, read_jsonl_documents(summary["documents_path"])

