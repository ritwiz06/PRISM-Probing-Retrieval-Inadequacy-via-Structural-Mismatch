from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from prism.ingest.build_kg import build_kg
from prism.public_corpus.build_public_corpus import build_public_corpus
from prism.public_graph.extract_graph import PublicGraphTriple, extract_public_graph
from prism.schemas import Triple
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_jsonl_triples

StructureMode = Literal["demo_kg", "public_graph", "mixed_public_demo"]

DEMO_KG_PATH = Path("data/processed/kg_triples.jsonl")
PUBLIC_GRAPH_PATH = Path("data/processed/public_graph_triples.jsonl")
PUBLIC_GRAPH_TTL_PATH = Path("data/processed/public_graph.ttl")
PUBLIC_GRAPH_METADATA_PATH = Path("data/processed/public_graph_metadata.json")
PUBLIC_MIXED_METADATA_PATH = Path("data/processed/public_graph_mixed_metadata.json")


def build_public_graph(
    corpus_path: str | Path = "data/processed/public_corpus.jsonl",
    output_path: str | Path = PUBLIC_GRAPH_PATH,
) -> dict[str, object]:
    resolved_corpus_path = Path(corpus_path)
    if not resolved_corpus_path.exists():
        build_public_corpus(resolved_corpus_path)
    documents = read_jsonl_documents(resolved_corpus_path)
    extracted = extract_public_graph(documents)
    triples = [item.to_triple() for item in extracted]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl_triples(output, triples)
    _write_turtle(triples, PUBLIC_GRAPH_TTL_PATH)
    _write_metadata(extracted, PUBLIC_GRAPH_METADATA_PATH)
    return _summary(extracted, output)


def load_public_structure_triples(mode: StructureMode) -> list[Triple]:
    if mode == "demo_kg":
        if not DEMO_KG_PATH.exists():
            build_kg()
        return read_jsonl_triples(DEMO_KG_PATH)
    if mode == "public_graph":
        if not PUBLIC_GRAPH_PATH.exists():
            build_public_graph()
        return read_jsonl_triples(PUBLIC_GRAPH_PATH)
    if mode == "mixed_public_demo":
        demo = load_public_structure_triples("demo_kg")
        public = load_public_structure_triples("public_graph")
        mixed, metadata = merge_public_and_demo_triples(demo, public)
        PUBLIC_MIXED_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return mixed
    raise ValueError(f"Unsupported public structure mode: {mode}")


def merge_public_and_demo_triples(demo: list[Triple], public: list[Triple]) -> tuple[list[Triple], dict[str, object]]:
    merged: dict[tuple[str, str, str], Triple] = {}
    provenance: dict[str, dict[str, object]] = {}
    for triple in demo:
        key = (triple.subject, triple.predicate, triple.object)
        merged[key] = triple
        provenance[triple.triple_id] = {"edge_source": "demo_kg", "source_doc_id": triple.source_doc_id}
    overlap = 0
    public_only = 0
    for triple in public:
        key = (triple.subject, triple.predicate, triple.object)
        if key in merged:
            overlap += 1
            existing = merged[key]
            merged[key] = Triple(existing.triple_id, existing.subject, existing.predicate, existing.object, f"{existing.source_doc_id}|public_graph:{triple.source_doc_id}")
            provenance[existing.triple_id] = {
                "edge_source": "mixed_overlap",
                "demo_source_doc_id": existing.source_doc_id,
                "public_source_doc_id": triple.source_doc_id,
                "public_triple_id": triple.triple_id,
            }
        else:
            public_only += 1
            merged[key] = triple
            provenance[triple.triple_id] = {"edge_source": "public_graph_only", "source_doc_id": triple.source_doc_id}
    triples = sorted(merged.values(), key=lambda item: item.triple_id)
    return triples, {"total": len(triples), "overlap": overlap, "public_only": public_only, "triple_provenance": provenance}


def _write_turtle(triples: list[Triple], path: Path) -> None:
    lines = [
        "@prefix prism: <https://prism.local/kg/> .",
        "",
        *[f"prism:{_ttl_name(triple.subject)} prism:{_ttl_name(triple.predicate)} prism:{_ttl_name(triple.object)} ." for triple in triples],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_metadata(extracted: list[PublicGraphTriple], path: Path) -> None:
    payload = {
        "total": len(extracted),
        "patterns": _pattern_counts(extracted),
        "average_confidence": sum(item.confidence for item in extracted) / len(extracted) if extracted else 0.0,
        "source_doc_count": len({item.source_doc_id for item in extracted}),
        "triples": [item.metadata() for item in extracted],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _summary(extracted: list[PublicGraphTriple], output: Path) -> dict[str, object]:
    return {
        "path": str(output),
        "ttl_path": str(PUBLIC_GRAPH_TTL_PATH),
        "metadata_path": str(PUBLIC_GRAPH_METADATA_PATH),
        "total": len(extracted),
        "patterns": _pattern_counts(extracted),
        "average_confidence": sum(item.confidence for item in extracted) / len(extracted) if extracted else 0.0,
        "source_doc_count": len({item.source_doc_id for item in extracted}),
    }


def _pattern_counts(extracted: list[PublicGraphTriple]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in extracted:
        counts[item.pattern] = counts.get(item.pattern, 0) + 1
    return dict(sorted(counts.items()))


def _ttl_name(value: str) -> str:
    return value.replace(" ", "_").replace("-", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PRISM's public graph from cached public raw documents.")
    parser.add_argument("--corpus", default="data/processed/public_corpus.jsonl")
    parser.add_argument("--output", default=str(PUBLIC_GRAPH_PATH))
    args = parser.parse_args()
    payload = build_public_graph(args.corpus, args.output)
    print(
        f"public_graph_triples={payload['total']} output={payload['path']} "
        f"ttl={payload['ttl_path']} metadata={payload['metadata_path']} "
        f"source_docs={payload['source_doc_count']} avg_confidence={payload['average_confidence']:.3f}"
    )
    print(f"pattern_counts={payload['patterns']}")


if __name__ == "__main__":
    main()
