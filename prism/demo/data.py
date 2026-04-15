from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from prism.app.pipeline import answer_query
from prism.eval.deductive_slice import load_deductive_queries
from prism.eval.lexical_slice import load_lexical_queries
from prism.eval.relational_slice import load_relational_queries
from prism.eval.semantic_slice import load_semantic_queries
from prism.utils import write_json


DEMO_PRESETS: tuple[tuple[str, str], ...] = (
    ("Lexical: RFC-7231", "RFC-7231"),
    ("Lexical: ICD-10 J18.9", "What is ICD-10 J18.9?"),
    ("Semantic: climate anxiety", "What feels like climate anxiety?"),
    ("Semantic: asphalt warmth pocket", "What is an asphalt warmth pocket?"),
    ("Deductive: mammal fly", "Can a mammal fly?"),
    ("Deductive: all mammals fly", "Are all mammals able to fly?"),
    ("Relational: bat to vertebrate", "What bridge connects bat and vertebrate?"),
    ("Relational: dolphin to echolocation", "What relation connects dolphin and echolocation?"),
)


def load_benchmark_queries() -> dict[str, list[dict[str, object]]]:
    return {
        "lexical": [_benchmark_row("lexical", item) for item in load_lexical_queries()],
        "semantic": [_benchmark_row("semantic", item) for item in load_semantic_queries()],
        "deductive": [_benchmark_row("deductive", item) for item in load_deductive_queries()],
        "relational": [_benchmark_row("relational", item) for item in load_relational_queries()],
    }


def curated_demo_queries() -> list[dict[str, object]]:
    benchmarks = load_benchmark_queries()
    by_query = {row["query"]: row for rows in benchmarks.values() for row in rows}
    rows: list[dict[str, object]] = []
    for label, query in DEMO_PRESETS:
        gold = dict(by_query.get(query, {"query": query}))
        gold["label"] = label
        rows.append(gold)
    return rows


def build_demo_view_model(
    query: str,
    gold: dict[str, object] | None = None,
    retrievers: dict[str, object] | None = None,
    top_k: int | None = None,
) -> dict[str, object]:
    payload = answer_query(query, top_k=top_k, retrievers=retrievers)
    gold_route = str(gold.get("gold_route")) if gold and gold.get("gold_route") else None
    gold_answer = str(gold.get("gold_answer")) if gold and gold.get("gold_answer") else None
    return {
        "query": query,
        "gold_route": gold_route,
        "gold_answer": gold_answer,
        "route_match": payload["selected_backend"] == gold_route if gold_route else None,
        "payload": payload,
        "score_rows": score_rows(payload),
        "evidence_rows": evidence_rows(payload),
        "backend_detail_rows": backend_detail_rows(payload),
    }


def export_demo_examples(path: str | Path = "data/eval/demo_examples.json") -> dict[str, object]:
    rows = []
    for item in curated_demo_queries():
        view_model = build_demo_view_model(str(item["query"]), gold=item, top_k=5)
        payload = view_model["payload"]
        rows.append(
            {
                "label": item.get("label"),
                "query": item["query"],
                "gold_route": view_model["gold_route"],
                "gold_answer": view_model["gold_answer"],
                "parsed_features": payload["parsed_features"],
                "ras_scores": payload["ras_scores"],
                "selected_backend": payload["selected_backend"],
                "answer": payload["answer"],
                "evidence": payload["top_evidence"],
                "reasoning_trace": payload["reasoning_trace"],
                "route_match": view_model["route_match"],
            }
        )
    output = {
        "example_count": len(rows),
        "route_families": sorted({str(row["selected_backend"]) for row in rows}),
        "examples": rows,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_json(path, output)
    return output


def score_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    selected = payload["selected_backend"]
    scores = payload["ras_scores"]
    return [
        {
            "backend": backend,
            "ras_score": score,
            "selected": backend == selected,
        }
        for backend, score in sorted(scores.items(), key=lambda item: item[1])
    ]


def evidence_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for rank, item in enumerate(payload["top_evidence"], start=1):
        metadata = item.get("metadata", {})
        rows.append(
            {
                "rank": rank,
                "id": item.get("item_id"),
                "score": item.get("score"),
                "type": item.get("source_type"),
                "snippet": item.get("content"),
                "metadata": metadata,
            }
        )
    return rows


def backend_detail_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for item in payload["top_evidence"]:
        metadata = item.get("metadata", {})
        rows.append(
            {
                "evidence_id": item.get("item_id"),
                "bm25_rank": metadata.get("bm25_rank") or metadata.get("rank") or metadata.get("raw_rank_bm25"),
                "dense_rank": metadata.get("dense_rank") or metadata.get("raw_rank_dense"),
                "kg_mode": metadata.get("query_mode"),
                "kg_triple_or_path": metadata.get("triple_id") or metadata.get("path_id"),
                "hybrid_components": metadata.get("component_ids"),
                "hybrid_backends": metadata.get("contributing_backends"),
                "fusion_method": metadata.get("fusion_method"),
                "evidence_type": metadata.get("evidence_type") or item.get("source_type"),
            }
        )
    return rows


def _benchmark_row(slice_name: str, item: object) -> dict[str, object]:
    if is_dataclass(item):
        row: dict[str, Any] = asdict(item)
    else:
        row = dict(item)
    row["slice"] = slice_name
    if "gold_evidence_doc_id" in row:
        row["gold_evidence_ids"] = [row["gold_evidence_doc_id"]]
    return row
