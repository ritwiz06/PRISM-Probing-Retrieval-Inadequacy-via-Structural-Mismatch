from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from prism.public_corpus.clean_and_chunk import load_clean_public_documents
from prism.public_corpus.enrich_documents import (
    PUBLIC_ENRICHED_METADATA_PATH,
    enrich_public_documents,
    write_enriched_metadata,
)
from prism.public_corpus.fetch_documents import RAW_PUBLIC_DIR, fetch_public_documents
from prism.public_corpus.source_registry import public_sources
from prism.utils import write_json, write_jsonl_documents

PUBLIC_CORPUS_PATH = Path("data/processed/public_corpus.jsonl")
PUBLIC_CORPUS_SUMMARY_PATH = Path("data/processed/public_corpus_summary.json")


def build_public_corpus(
    output_path: str | Path = PUBLIC_CORPUS_PATH,
    refresh: bool = False,
) -> Path:
    sources = public_sources()
    fetch_summary = fetch_public_documents(RAW_PUBLIC_DIR, refresh=refresh, sources=sources)
    documents = load_clean_public_documents(RAW_PUBLIC_DIR)
    enriched_metadata = enrich_public_documents(RAW_PUBLIC_DIR)
    write_enriched_metadata(enriched_metadata, PUBLIC_ENRICHED_METADATA_PATH)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl_documents(output, documents)
    family_counts = Counter(_source_part(document.source, 2) for document in documents)
    type_counts = Counter(_source_part(document.source, 1) for document in documents)
    content_status_counts = Counter(_fetch_status(document.source) for document in documents)
    summary = {
        "path": str(output),
        "document_count": len(documents),
        "target_source_count": len(sources),
        "fetch_summary": {
            "fetched": fetch_summary["fetched"],
            "cached": fetch_summary["cached"],
            "fallback_snapshot": fetch_summary["fallback_snapshot"],
            "skipped": fetch_summary["skipped"],
            "raw_dir": fetch_summary["raw_dir"],
        },
        "content_status_counts": dict(sorted(content_status_counts.items())),
        "counts_by_route_family": dict(sorted(family_counts.items())),
        "counts_by_source_type": dict(sorted(type_counts.items())),
        "enriched_metadata_path": str(PUBLIC_ENRICHED_METADATA_PATH),
        "identifier_document_count": sum(1 for row in enriched_metadata.values() if row.canonical_identifiers),
    }
    write_json(PUBLIC_CORPUS_SUMMARY_PATH, summary)
    return output


def _source_part(source: str, index: int) -> str:
    parts = source.split(":")
    return parts[index] if len(parts) > index else "unknown"


def _fetch_status(source: str) -> str:
    marker = "fetch_status="
    if marker not in source:
        return "unknown"
    return source.split(marker, 1)[1].split(":", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's cached public raw-document corpus.")
    parser.add_argument("--refresh", action="store_true", help="Attempt to refetch source URLs instead of reusing cache.")
    args = parser.parse_args()
    path = build_public_corpus(refresh=args.refresh)
    import json

    summary = json.loads(PUBLIC_CORPUS_SUMMARY_PATH.read_text(encoding="utf-8"))
    print(
        "public_corpus "
        f"path={path} documents={summary['document_count']} target_sources={summary['target_source_count']} "
        f"families={summary['counts_by_route_family']} fetch={summary['fetch_summary']}"
    )


if __name__ == "__main__":
    main()
