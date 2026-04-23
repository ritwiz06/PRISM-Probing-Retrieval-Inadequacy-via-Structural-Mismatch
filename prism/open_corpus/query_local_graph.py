from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

from prism.schemas import Document, Triple
from prism.utils import write_jsonl_triples


@dataclass(frozen=True, slots=True)
class QueryLocalGraph:
    query: str
    triples: list[Triple]
    metadata: dict[str, object]


ENTITY_PATTERN = r"([A-Z][A-Za-z0-9._§-]*(?:\s+[A-Z][A-Za-z0-9._§-]*){0,3}|[a-z][a-z0-9._§-]+)"
PATTERNS: tuple[tuple[str, str], ...] = (
    (rf"{ENTITY_PATTERN}\s+is\s+a[n]?\s+{ENTITY_PATTERN}", "is_a"),
    (rf"{ENTITY_PATTERN}\s+is\s+an?\s+example\s+of\s+{ENTITY_PATTERN}", "is_a"),
    (rf"{ENTITY_PATTERN}\s+has\s+(?:a\s+)?(?:property|feature|adaptation)\s+(?:of\s+)?{ENTITY_PATTERN}", "has_property"),
    (rf"{ENTITY_PATTERN}\s+(?:uses|use)\s+{ENTITY_PATTERN}", "uses"),
    (rf"{ENTITY_PATTERN}\s+(?:connects|links|bridges)\s+(?:to\s+)?{ENTITY_PATTERN}", "connects_to"),
    (rf"{ENTITY_PATTERN}\s+(?:enables|allows)\s+{ENTITY_PATTERN}", "enables"),
)


def build_query_local_graph(query: str, documents: list[Document], *, max_triples: int = 80) -> QueryLocalGraph:
    triples: list[Triple] = []
    seen: set[tuple[str, str, str]] = set()
    for document in documents:
        for predicate_pattern, predicate in PATTERNS:
            for match in re.finditer(predicate_pattern, document.text):
                subject = normalize_entity(match.group(1))
                object_ = normalize_entity(match.group(2))
                if not subject or not object_ or subject == object_:
                    continue
                key = (subject, predicate, object_)
                if key in seen:
                    continue
                seen.add(key)
                triples.append(
                    Triple(
                        triple_id=f"qlg_{len(triples):04d}_{document.doc_id}",
                        subject=subject,
                        predicate=predicate,
                        object=object_,
                        source_doc_id=document.doc_id,
                    )
                )
                if len(triples) >= max_triples:
                    return _graph(query, triples, documents)
    return _graph(query, triples, documents)


def export_query_local_graph(graph: QueryLocalGraph, output_dir: str | Path, name: str) -> dict[str, object]:
    target = Path(output_dir) / "query_graphs"
    target.mkdir(parents=True, exist_ok=True)
    triples_path = target / f"{name}_triples.jsonl"
    json_path = target / f"{name}_graph.json"
    write_jsonl_triples(triples_path, graph.triples)
    json_path.write_text(
        json.dumps(
            {
                "query": graph.query,
                "triple_count": len(graph.triples),
                "triples": [asdict(triple) for triple in graph.triples],
                "metadata": graph.metadata,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"triples_path": str(triples_path), "json_path": str(json_path), "triple_count": len(graph.triples)}


def normalize_entity(entity: str) -> str:
    entity = re.sub(r"^(?:a|an|the)\s+", "", entity.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9._§-]+", "_", entity.lower()).strip("_")
    aliases = {"bats": "bat", "mammals": "mammal", "vertebrates": "vertebrate", "wings": "wing"}
    return aliases.get(cleaned, cleaned)


def _graph(query: str, triples: list[Triple], documents: list[Document]) -> QueryLocalGraph:
    return QueryLocalGraph(
        query=query,
        triples=triples,
        metadata={
            "backend_type": "query_local_graph",
            "document_count": len(documents),
            "triple_count": len(triples),
            "extraction": "lightweight regex patterns with source document provenance",
        },
    )
