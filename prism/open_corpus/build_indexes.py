from __future__ import annotations

from pathlib import Path

from prism.config import load_config
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.schemas import Document
from prism.utils import write_json


def build_runtime_indexes(documents: list[Document], output_dir: str | Path) -> dict[str, object]:
    target = Path(output_dir)
    index_dir = target / "indexes"
    index_dir.mkdir(parents=True, exist_ok=True)
    bm25_path = BM25Retriever.build(documents).save(index_dir / "bm25.pkl")
    dense = DenseRetriever.build(documents, config=load_config().retrieval)
    dense_path = dense.save(index_dir / "dense.pkl")
    metadata = {
        "document_count": len(documents),
        "bm25_index": str(bm25_path),
        "dense_index": str(dense_path),
        "dense_backend": getattr(dense, "active_backend", "unknown"),
    }
    write_json(index_dir / "index_metadata.json", metadata)
    return metadata

