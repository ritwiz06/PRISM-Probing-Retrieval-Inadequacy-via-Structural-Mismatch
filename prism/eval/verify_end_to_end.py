from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from prism.app.pipeline import answer_query
from prism.eval.deductive_slice import load_deductive_queries
from prism.eval.lexical_slice import load_lexical_queries
from prism.eval.relational_slice import load_relational_queries
from prism.eval.semantic_slice import load_semantic_queries
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.utils import write_json


def verify_end_to_end() -> dict[str, object]:
    build_corpus()
    build_kg()
    rows: list[dict[str, object]] = []
    slice_totals: Counter[str] = Counter()
    route_correct: Counter[str] = Counter()
    evidence_hits: Counter[str] = Counter()
    answer_matches: Counter[str] = Counter()
    trace_count = 0
    confusion: Counter[str] = Counter()

    for slice_name, items in _benchmark_items():
        for item in items:
            gold_route = item.gold_route
            gold_answer = item.gold_answer
            gold_evidence = _gold_evidence(item)
            top_k = 5 if slice_name == "relational" else 3
            payload = answer_query(item.query, top_k=top_k)
            predicted = str(payload["selected_backend"])
            answer = payload["answer"]
            evidence_ids = _payload_evidence_ids(payload)
            route_ok = predicted == gold_route
            evidence_ok = bool(set(gold_evidence) & evidence_ids)
            if slice_name == "relational":
                evidence_ok = set(gold_evidence).issubset(evidence_ids)
            answer_ok = _answer_matches(str(answer["final_answer"]), gold_answer)
            has_trace = bool(payload["reasoning_trace"])
            trace_count += int(has_trace)
            slice_totals[slice_name] += 1
            route_correct[slice_name] += int(route_ok)
            evidence_hits[slice_name] += int(evidence_ok)
            answer_matches[slice_name] += int(answer_ok)
            confusion[f"{gold_route}->{predicted}"] += 1
            rows.append(
                {
                    "slice": slice_name,
                    "query": item.query,
                    "gold_route": gold_route,
                    "predicted_route": predicted,
                    "route_correct": route_ok,
                    "gold_answer": gold_answer,
                    "answer": answer["final_answer"],
                    "answer_match": answer_ok,
                    "gold_evidence": gold_evidence,
                    "evidence_ids": sorted(evidence_ids),
                    "evidence_hit": evidence_ok,
                    "trace_generated": has_trace,
                    "trace_sample": payload["reasoning_trace"][:2],
                }
            )

    total = sum(slice_totals.values())
    payload = {
        "total": total,
        "route_accuracy": sum(route_correct.values()) / total,
        "evidence_hit_at_k": sum(evidence_hits.values()) / total,
        "answer_match_total": sum(answer_matches.values()),
        "trace_count": trace_count,
        "per_slice": {
            name: {
                "total": slice_totals[name],
                "route_accuracy": route_correct[name] / slice_totals[name],
                "evidence_hit_at_k": evidence_hits[name],
                "answer_matches": answer_matches[name],
            }
            for name in sorted(slice_totals)
        },
        "confusion": dict(confusion),
        "sample_traces": [row for row in rows[:4]],
        "results": rows,
        "passed": (
            sum(route_correct.values()) / total >= 0.85
            and answer_matches["lexical"] >= 18
            and answer_matches["semantic"] >= 14
            and answer_matches["deductive"] >= 16
            and answer_matches["relational"] >= 14
            and trace_count == total
        ),
    }
    output_path = Path("data/eval/end_to_end_verification.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def _benchmark_items() -> Iterable[tuple[str, list[object]]]:
    yield "lexical", load_lexical_queries()
    yield "semantic", load_semantic_queries()
    yield "deductive", load_deductive_queries()
    yield "relational", load_relational_queries()


def _gold_evidence(item: object) -> list[str]:
    if hasattr(item, "gold_evidence_doc_id"):
        return [getattr(item, "gold_evidence_doc_id")]
    return list(getattr(item, "gold_evidence_ids"))


def _payload_evidence_ids(payload: dict[str, object]) -> set[str]:
    ids: set[str] = set()
    for item in payload["top_evidence"]:
        ids.add(item["item_id"])
        metadata = item["metadata"]
        for key in ("component_ids", "triple_id", "path_id", "parent_doc_id", "chunk_id"):
            for part in str(metadata.get(key, "")).split(","):
                if part:
                    ids.add(part)
    return ids


def _answer_matches(answer: str, gold: str) -> bool:
    answer_norm = _normalize(answer)
    gold_norm = _normalize(gold)
    if not gold_norm:
        return False
    if gold_norm in answer_norm:
        return True
    gold_tokens = [token for token in gold_norm.split() if token not in {"the", "a", "an", "and", "or", "to", "of", "in"}]
    if not gold_tokens:
        return False
    overlap = sum(1 for token in gold_tokens if token in answer_norm)
    return overlap / len(gold_tokens) >= 0.5


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9§._:/ -]+", " ", text.lower())).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify PRISM end-to-end answers across all slices.")
    parser.parse_args()
    payload = verify_end_to_end()
    print(
        f"end_to_end_total={payload['total']} route_accuracy={payload['route_accuracy']:.3f} "
        f"evidence_hit@k={payload['evidence_hit_at_k']:.3f} traces={payload['trace_count']}/{payload['total']} "
        f"answers={payload['answer_match_total']}/{payload['total']} passed={payload['passed']}"
    )
    for name, row in payload["per_slice"].items():
        print(
            f"{name}: route_accuracy={row['route_accuracy']:.2f} "
            f"evidence_hit@k={row['evidence_hit_at_k']}/{row['total']} "
            f"answer_matches={row['answer_matches']}/{row['total']}"
        )


if __name__ == "__main__":
    main()
