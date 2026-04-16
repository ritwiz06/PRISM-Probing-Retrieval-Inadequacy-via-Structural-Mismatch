from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.kg_extraction.extract_triples import ExtractedTriple, extract_triples_from_documents
from prism.schemas import Triple
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_jsonl_triples

KGMode = Literal["curated", "extracted", "mixed"]
CURATED_KG_PATH = Path("data/processed/kg_triples.jsonl")
EXTRACTED_KG_PATH = Path("data/processed/kg_extracted_triples.jsonl")
EXTRACTED_TTL_PATH = Path("data/processed/kg_extracted.ttl")
EXTRACTED_METADATA_PATH = Path("data/processed/kg_extracted_metadata.json")
MIXED_METADATA_PATH = Path("data/processed/kg_mixed_metadata.json")


def build_extracted_kg(
    corpus_path: str | Path = "data/processed/corpus.jsonl",
    output_path: str | Path = EXTRACTED_KG_PATH,
) -> dict[str, object]:
    resolved_corpus_path = Path(corpus_path)
    if not resolved_corpus_path.exists():
        build_corpus(output_path=str(resolved_corpus_path))
    documents = read_jsonl_documents(resolved_corpus_path)
    extracted = extract_triples_from_documents(documents)
    triples = [item.to_triple() for item in extracted]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl_triples(output, triples)
    _write_turtle(triples, EXTRACTED_TTL_PATH)
    _write_metadata(extracted, EXTRACTED_METADATA_PATH)
    summary = _summary(extracted, output)
    return summary


def load_kg_triples_for_mode(mode: KGMode) -> list[Triple]:
    if mode == "curated":
        if not CURATED_KG_PATH.exists():
            build_kg()
        return read_jsonl_triples(CURATED_KG_PATH)
    if mode == "extracted":
        if not EXTRACTED_KG_PATH.exists():
            build_extracted_kg()
        return read_jsonl_triples(EXTRACTED_KG_PATH)
    if mode == "mixed":
        curated = load_kg_triples_for_mode("curated")
        extracted = load_kg_triples_for_mode("extracted")
        mixed, metadata = merge_triples(curated, extracted)
        MIXED_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return mixed
    raise ValueError(f"Unsupported KG mode: {mode}")


def merge_triples(curated: list[Triple], extracted: list[Triple]) -> tuple[list[Triple], dict[str, object]]:
    merged: dict[tuple[str, str, str], Triple] = {}
    provenance: dict[str, dict[str, object]] = {}
    for triple in curated:
        key = (triple.subject, triple.predicate, triple.object)
        merged[key] = triple
        provenance[triple.triple_id] = {"mode": "curated", "source_doc_id": triple.source_doc_id}
    overlap = 0
    extracted_only = 0
    for triple in extracted:
        key = (triple.subject, triple.predicate, triple.object)
        if key in merged:
            existing = merged[key]
            overlap += 1
            merged[key] = Triple(
                triple_id=existing.triple_id,
                subject=existing.subject,
                predicate=existing.predicate,
                object=existing.object,
                source_doc_id=f"{existing.source_doc_id}|extracted:{triple.source_doc_id}",
            )
            provenance[existing.triple_id] = {
                "mode": "mixed_overlap",
                "curated_source_doc_id": existing.source_doc_id,
                "extracted_source_doc_id": triple.source_doc_id,
                "extracted_triple_id": triple.triple_id,
            }
        else:
            extracted_only += 1
            merged[key] = triple
            provenance[triple.triple_id] = {"mode": "extracted_only", "source_doc_id": triple.source_doc_id}
    triples = sorted(merged.values(), key=lambda item: item.triple_id)
    return triples, {"total": len(triples), "overlap": overlap, "extracted_only": extracted_only, "triple_provenance": provenance}


def _write_turtle(triples: list[Triple], path: Path) -> None:
    lines = [
        "@prefix prism: <https://prism.local/kg/> .",
        "",
        *[f"prism:{_ttl_name(triple.subject)} prism:{_ttl_name(triple.predicate)} prism:{_ttl_name(triple.object)} ." for triple in triples],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_metadata(extracted: list[ExtractedTriple], path: Path) -> None:
    payload = {
        "total": len(extracted),
        "patterns": _pattern_counts(extracted),
        "average_confidence": sum(item.confidence for item in extracted) / len(extracted) if extracted else 0.0,
        "triples": [item.metadata() for item in extracted],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _summary(extracted: list[ExtractedTriple], output: Path) -> dict[str, object]:
    return {
        "path": str(output),
        "ttl_path": str(EXTRACTED_TTL_PATH),
        "metadata_path": str(EXTRACTED_METADATA_PATH),
        "total": len(extracted),
        "patterns": _pattern_counts(extracted),
        "average_confidence": sum(item.confidence for item in extracted) / len(extracted) if extracted else 0.0,
    }


def _pattern_counts(extracted: list[ExtractedTriple]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in extracted:
        counts[item.pattern] = counts.get(item.pattern, 0) + 1
    return dict(sorted(counts.items()))


def _ttl_name(value: str) -> str:
    return value.replace(" ", "_").replace("-", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's rule-extracted KG from the local corpus.")
    parser.add_argument("--corpus", default="data/processed/corpus.jsonl")
    parser.add_argument("--output", default=str(EXTRACTED_KG_PATH))
    args = parser.parse_args()
    payload = build_extracted_kg(args.corpus, args.output)
    print(
        f"kg_extracted_triples={payload['total']} output={payload['path']} "
        f"ttl={payload['ttl_path']} metadata={payload['metadata_path']} "
        f"avg_confidence={payload['average_confidence']:.3f}"
    )
    print(f"pattern_counts={payload['patterns']}")


if __name__ == "__main__":
    main()
