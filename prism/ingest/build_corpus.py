from __future__ import annotations

import argparse
import logging
from pathlib import Path

from prism.config import load_config
from prism.ingest import formal_docs_fetch, wikipedia_fetch
from prism.logging_utils import configure_logging
from prism.schemas import Document
from prism.utils import ensure_directories, write_jsonl_documents

LOGGER = logging.getLogger(__name__)


def build_corpus(output_path: str | None = None, refresh: bool = False) -> Path:
    config = load_config()
    configure_logging(config.log_level)
    ensure_directories([config.paths.raw_dir, config.paths.processed_dir, config.paths.indices_dir, config.paths.eval_dir])

    documents: list[Document] = wikipedia_fetch.fetch_documents(raw_dir=config.paths.raw_dir, refresh=refresh) + formal_docs_fetch.fetch_documents()
    documents = sorted(documents, key=lambda document: document.doc_id)
    corpus_path = Path(output_path or Path(config.paths.processed_dir) / "corpus.jsonl")
    write_jsonl_documents(corpus_path, documents)
    LOGGER.info("Wrote %s corpus documents to %s", len(documents), corpus_path)
    return corpus_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local PRISM corpus.")
    parser.add_argument("--output", default=None, help="Optional output path for corpus JSONL.")
    parser.add_argument("--refresh", action="store_true", help="Rebuild the curated raw-page cache.")
    args = parser.parse_args()
    path = build_corpus(output_path=args.output, refresh=args.refresh)
    print(f"corpus_path={path}")


if __name__ == "__main__":
    main()
