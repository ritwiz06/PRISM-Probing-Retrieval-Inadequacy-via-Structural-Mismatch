from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from prism.open_corpus.normalize_documents import document_metadata_payload, normalize_raw_document
from prism.open_corpus.source_packs import get_source_pack, list_source_packs
from prism.utils import write_json, write_jsonl_documents

RUNTIME_ROOT = Path("data/runtime_corpora")


def build_source_pack(pack: str, *, output_root: str | Path = RUNTIME_ROOT) -> dict[str, object]:
    source_pack = get_source_pack(pack)
    normalized = [
        normalize_raw_document(
            text=item.text,
            title=item.title,
            source_type=f"source_pack:{source_pack.name}",
            provenance=item.source_url,
            doc_id=item.doc_id,
            metadata={"route_family_hint": item.route_family_hint, "source_url": item.source_url},
        )
        for item in source_pack.documents
    ]
    output_dir = Path(output_root) / f"source_pack_{pack}"
    output_dir.mkdir(parents=True, exist_ok=True)
    documents_path = output_dir / "documents.jsonl"
    metadata_path = output_dir / "metadata.json"
    write_jsonl_documents(documents_path, [entry.document for entry in normalized])
    metadata = document_metadata_payload(f"source_pack:{pack}", normalized)
    metadata.update(
        {
            "pack": asdict(source_pack),
            "documents_path": str(documents_path),
            "output_dir": str(output_dir),
            "cache_policy": "Embedded source-list fallback; URL fetching can be layered separately without changing this artifact.",
        }
    )
    write_json(metadata_path, metadata)
    return {
        "pack": pack,
        "document_count": len(normalized),
        "output_dir": str(output_dir),
        "documents_path": str(documents_path),
        "metadata_path": str(metadata_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an optional PRISM open-corpus source pack.")
    parser.add_argument("--pack", required=True, choices=list_source_packs())
    args = parser.parse_args()
    payload = build_source_pack(args.pack)
    print(
        "source_pack_built "
        f"pack={payload['pack']} documents={payload['document_count']} "
        f"documents_path={payload['documents_path']} metadata={payload['metadata_path']}"
    )


if __name__ == "__main__":
    main()

