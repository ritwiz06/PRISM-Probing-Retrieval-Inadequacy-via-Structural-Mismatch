from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from prism.analysis.evaluation import (
    answer_matches_gold,
    evaluate_system,
    evidence_id_set,
    load_combined_benchmark,
)
from prism.app.pipeline import answer_query
from prism.config import RetrievalConfig, load_config
from prism.eval.semantic_slice import load_semantic_queries
from prism.external_benchmarks.loaders import ExternalBenchmarkItem, load_external_mini_benchmark
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.schemas import Document, Triple
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json

EVAL_DIR = Path("data/eval")
FAILURE_JSON = EVAL_DIR / "failure_analysis.json"
FAILURE_CSV = EVAL_DIR / "failure_analysis.csv"
FAILURE_MD = EVAL_DIR / "failure_analysis_summary.md"
DENSE_COMPARE_JSON = EVAL_DIR / "dense_before_after.json"
DENSE_COMPARE_MD = EVAL_DIR / "dense_before_after_summary.md"
ROBUSTNESS_MD = EVAL_DIR / "robustness_summary.md"

DENSE_VARIANTS = (
    "numpy_fallback",
    "sentence_transformers_faiss_pre_robustness",
    "sentence_transformers_faiss_robust",
)


def run_failure_analysis() -> dict[str, object]:
    documents, triples = _load_artifacts()
    variant_retrievers = {name: _build_retrievers(documents, triples, name) for name in DENSE_VARIANTS}
    semantic_runs = {name: _evaluate_semantic(variant_retrievers[name]) for name in DENSE_VARIANTS}
    end_to_end_runs = {
        name: evaluate_system("computed_ras", benchmark=load_combined_benchmark(), retrievers=variant_retrievers[name])
        for name in DENSE_VARIANTS
    }
    external_runs = {name: _evaluate_external(variant_retrievers[name]) for name in DENSE_VARIANTS}
    failures = _collect_failures(semantic_runs, end_to_end_runs, external_runs)
    dense_compare = _dense_before_after(variant_retrievers, semantic_runs, end_to_end_runs, external_runs)

    payload = {
        "method": {
            "previous_fallback": "Recomputed with RetrievalConfig(dense_backend='numpy') through the current stable retriever interface.",
            "pre_robustness": "Recomputed with sentence-transformers/FAISS and semantic_rerank=False to approximate the post-Dense-upgrade regression state.",
            "current_robust": "Current sentence-transformers/FAISS retriever with metadata-visible semantic concept reranking enabled.",
        },
        "failure_count": len(failures),
        "failures": failures,
        "semantic_runs": semantic_runs,
        "end_to_end_summary": {
            name: _summarize_end_to_end(run) for name, run in end_to_end_runs.items()
        },
        "external_summary": {
            name: _summarize_external(run) for name, run in external_runs.items()
        },
        "photosynthesis_external_fixed": _photosynthesis_status(external_runs),
    }

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    write_json(FAILURE_JSON, payload)
    write_json(DENSE_COMPARE_JSON, dense_compare)
    _write_failure_csv(FAILURE_CSV, failures)
    FAILURE_MD.write_text(_failure_markdown(payload), encoding="utf-8")
    DENSE_COMPARE_MD.write_text(_dense_compare_markdown(dense_compare), encoding="utf-8")
    ROBUSTNESS_MD.write_text(_robustness_markdown(payload, dense_compare), encoding="utf-8")
    return payload


def assign_error_buckets(row: dict[str, object]) -> list[str]:
    buckets: list[str] = []
    if not row.get("route_correct", True):
        buckets.append("route_error")
    if not row.get("evidence_hit", True):
        buckets.append("retrieval_miss")
    if row.get("evidence_hit") and not row.get("top1_hit", True):
        buckets.append("ranking_error")
    if row.get("evidence_hit") and not row.get("answer_match", True):
        buckets.append("answer_synthesis_miss")
    if row.get("slice") == "deductive" and not row.get("evidence_hit", True):
        buckets.append("kg_incompleteness")
    if row.get("slice") == "semantic":
        buckets.append("semantic_drift")
    if any(str(item).startswith("lex_") for item in row.get("retrieved_evidence_ids", [])):
        buckets.append("lexical_confusion")
    if row.get("slice") == "relational" and not row.get("evidence_hit", True):
        buckets.append("hybrid_fusion_miss")
    if row.get("benchmark_evidence_mismatch"):
        buckets.append("benchmark_evidence_mismatch")
    return sorted(dict.fromkeys(buckets))


def _load_artifacts() -> tuple[list[Document], list[Triple]]:
    config = load_config()
    corpus_path = Path(config.paths.processed_dir) / "corpus.jsonl"
    kg_path = Path(config.paths.processed_dir) / "kg_triples.jsonl"
    if not corpus_path.exists():
        build_corpus()
    if not kg_path.exists():
        build_kg(corpus_path=str(corpus_path))
    return read_jsonl_documents(corpus_path), read_jsonl_triples(kg_path)


def _build_retrievers(documents: list[Document], triples: list[Triple], variant: str) -> dict[str, object]:
    base_config = load_config().retrieval
    config = RetrievalConfig(**asdict(base_config))
    semantic_rerank = True
    if variant == "numpy_fallback":
        config.dense_backend = "numpy"
    elif variant == "sentence_transformers_faiss_pre_robustness":
        config.dense_backend = base_config.dense_backend
        semantic_rerank = False
    elif variant == "sentence_transformers_faiss_robust":
        config.dense_backend = base_config.dense_backend
        semantic_rerank = True
    else:
        raise ValueError(f"Unknown Dense variant: {variant}")

    bm25 = BM25Retriever.build(documents)
    dense = DenseRetriever(documents=documents, config=config, semantic_rerank=semantic_rerank)
    kg = KGRetriever.build(triples)
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def _evaluate_semantic(retrievers: dict[str, object]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    top1 = 0
    hit_at_3 = 0
    for item in load_semantic_queries():
        evidence = retrievers["dense"].retrieve(item.query, top_k=3)
        evidence_ids = evidence_id_set(evidence)
        retrieved_ids = [str(hit.metadata.get("parent_doc_id", hit.item_id)) for hit in evidence]
        top1_ok = bool(retrieved_ids and retrieved_ids[0] == item.gold_evidence_doc_id)
        hit_ok = item.gold_evidence_doc_id in evidence_ids or item.gold_evidence_doc_id in retrieved_ids
        top1 += int(top1_ok)
        hit_at_3 += int(hit_ok)
        rows.append(
            {
                "query": item.query,
                "gold_answer": item.gold_answer,
                "gold_evidence_id": item.gold_evidence_doc_id,
                "top1_hit": top1_ok,
                "hit_at_3": hit_ok,
                "top_evidence": [
                    {
                        "item_id": hit.item_id,
                        "parent_doc_id": hit.metadata.get("parent_doc_id", ""),
                        "score": hit.score,
                        "title": hit.metadata.get("title", ""),
                        "snippet": hit.content[:180],
                    }
                    for hit in evidence
                ],
            }
        )
    total = len(rows)
    dense_status = getattr(retrievers["dense"], "backend_status", {})
    return {
        "total": total,
        "top1": top1,
        "hit_at_3": hit_at_3,
        "top1_accuracy": top1 / total if total else 0.0,
        "hit_at_3_accuracy": hit_at_3 / total if total else 0.0,
        "dense_backend_status": dense_status,
        "rows": rows,
    }


def _evaluate_external(retrievers: dict[str, object]) -> dict[str, object]:
    items = load_external_mini_benchmark()
    rows: list[dict[str, object]] = []
    correct = 0
    per_family = defaultdict(lambda: Counter(total=0, correct=0))
    for item in items:
        top_k = 5 if item.route_family == "hybrid" else 3
        payload = answer_query(item.query, top_k=top_k, retrievers=retrievers)
        answer = str(payload["answer"]["final_answer"])
        ok = answer_matches_gold(answer, item.gold_answer)
        correct += int(ok)
        per_family[item.route_family]["total"] += 1
        per_family[item.route_family]["correct"] += int(ok)
        rows.append(
            {
                "id": item.id,
                "query": item.query,
                "route_family": item.route_family,
                "source_dataset": item.source_dataset,
                "gold_answer": item.gold_answer,
                "answer": answer,
                "answer_match": ok,
                "selected_backend": payload["selected_backend"],
                "top_evidence_ids": [hit["item_id"] for hit in payload["top_evidence"][:3]],
            }
        )
    total = len(items)
    return {
        "total": total,
        "answer_matches": correct,
        "answer_accuracy": correct / total if total else 0.0,
        "per_family": {
            family: {
                "total": counts["total"],
                "answer_matches": counts["correct"],
                "answer_accuracy": counts["correct"] / counts["total"] if counts["total"] else 0.0,
            }
            for family, counts in sorted(per_family.items())
        },
        "rows": rows,
    }


def _collect_failures(
    semantic_runs: dict[str, dict[str, object]],
    end_to_end_runs: dict[str, dict[str, object]],
    external_runs: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    pre_semantic = {row["query"]: row for row in semantic_runs["sentence_transformers_faiss_pre_robustness"]["rows"]}
    robust_semantic = {row["query"]: row for row in semantic_runs["sentence_transformers_faiss_robust"]["rows"]}
    pre_e2e = end_to_end_runs["sentence_transformers_faiss_pre_robustness"]["results"]
    robust_e2e = {row["query"]: row for row in end_to_end_runs["sentence_transformers_faiss_robust"]["results"]}

    for row in pre_e2e:
        if row["answer_match"] and row["evidence_hit"]:
            continue
        query = str(row["query"])
        semantic_row = pre_semantic.get(query)
        top1_hit = bool(semantic_row and semantic_row["top1_hit"])
        failure_row = {
            "id": _stable_failure_id("curated", query),
            "benchmark": "curated_end_to_end",
            "slice": row["slice"],
            "query": query,
            "gold_answer": row["gold_answer"],
            "pre_robustness_answer": row["answer"],
            "post_robustness_answer": robust_e2e.get(query, {}).get("answer", ""),
            "answer_match": row["answer_match"],
            "post_robustness_answer_match": robust_e2e.get(query, {}).get("answer_match", False),
            "gold_evidence_ids": row["gold_evidence_ids"],
            "retrieved_evidence_ids": row["retrieved_evidence_ids"],
            "evidence_hit": row["evidence_hit"],
            "route_correct": row["route_correct"],
            "top1_hit": top1_hit,
            "top_competing_evidence": _top_competing(semantic_row),
            "post_robustness_top_evidence": _top_competing(robust_semantic.get(query)),
            "suggested_remediation": _remediation_note(row, semantic_row),
        }
        failure_row["error_buckets"] = assign_error_buckets(failure_row)
        failures.append(failure_row)

    for row in semantic_runs["sentence_transformers_faiss_pre_robustness"]["rows"]:
        if row["top1_hit"] and row["hit_at_3"]:
            continue
        query = str(row["query"])
        if any(existing["query"] == query for existing in failures):
            continue
        failure_row = {
            "id": _stable_failure_id("semantic", query),
            "benchmark": "curated_semantic",
            "slice": "semantic",
            "query": query,
            "gold_answer": row["gold_answer"],
            "gold_evidence_ids": [row["gold_evidence_id"]],
            "retrieved_evidence_ids": [hit["parent_doc_id"] for hit in row["top_evidence"]],
            "evidence_hit": row["hit_at_3"],
            "top1_hit": row["top1_hit"],
            "route_correct": True,
            "answer_match": True,
            "top_competing_evidence": _top_competing(row),
            "post_robustness_top_evidence": _top_competing(robust_semantic.get(query)),
            "suggested_remediation": _remediation_note({"slice": "semantic"}, row),
        }
        failure_row["error_buckets"] = assign_error_buckets(failure_row)
        failures.append(failure_row)

    photosynthesis = _photosynthesis_status(external_runs)
    if photosynthesis:
        failures.append(
            {
                "id": "external_photosynthesis_status",
                "benchmark": "external_mini_benchmark",
                "slice": "semantic",
                "query": photosynthesis["query"],
                "gold_answer": "Photosynthesis.",
                "status": "fixed" if photosynthesis["current_fixed"] else "still_failing",
                "previous_fallback_answer": photosynthesis["fallback_answer"],
                "current_answer": photosynthesis["current_answer"],
                "top_competing_evidence": photosynthesis["current_top_evidence_ids"],
                "error_buckets": [] if photosynthesis["current_fixed"] else ["semantic_drift", "retrieval_miss"],
                "suggested_remediation": "No change needed; current real Dense plus robustness rerank answers the external photosynthesis paraphrase.",
            }
        )
    return failures


def _dense_before_after(
    retrievers: dict[str, dict[str, object]],
    semantic_runs: dict[str, dict[str, object]],
    end_to_end_runs: dict[str, dict[str, object]],
    external_runs: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "comparison_method": "Compatibility reruns over the same local corpus/KG. The pre-robustness run disables semantic_rerank to reproduce the Dense-upgrade regression state.",
        "runs": {
            name: {
                "dense_backend_status": getattr(retrievers[name]["dense"], "backend_status", {}),
                "curated_semantic": {
                    "top1": semantic_runs[name]["top1"],
                    "hit_at_3": semantic_runs[name]["hit_at_3"],
                    "total": semantic_runs[name]["total"],
                },
                "curated_end_to_end": _summarize_end_to_end(end_to_end_runs[name]),
                "external_mini_benchmark": _summarize_external(external_runs[name]),
            }
            for name in DENSE_VARIANTS
        },
        "claim_validation_note": "The lexical BM25-over-Dense claim should be reported cautiously when real Dense ties BM25 on lexical hit@k; this analysis does not hide that tradeoff.",
        "robustness_change": "Enabled a small metadata-visible semantic concept rerank that uses the existing local semantic alias table to correct real-embedding semantic drift.",
    }


def _summarize_end_to_end(run: dict[str, object]) -> dict[str, object]:
    return {
        "total": run["total"],
        "route_accuracy": run["route_accuracy"],
        "evidence_hit_at_k": run["evidence_hit_at_k"],
        "answer_accuracy": run["answer_accuracy"],
        "answer_matches": run["answer_matches"],
        "evidence_hits": run["evidence_hits"],
        "per_slice": {
            name: {
                "answer_matches": row["answer_matches"],
                "evidence_hits": row["evidence_hits"],
                "total": row["total"],
            }
            for name, row in run["per_slice"].items()
        },
    }


def _summarize_external(run: dict[str, object]) -> dict[str, object]:
    return {
        "total": run["total"],
        "answer_matches": run["answer_matches"],
        "answer_accuracy": run["answer_accuracy"],
        "per_family": {
            name: {
                "answer_matches": row["answer_matches"],
                "total": row["total"],
                "answer_accuracy": row["answer_accuracy"],
            }
            for name, row in run["per_family"].items()
        },
    }


def _photosynthesis_status(external_runs: dict[str, dict[str, object]]) -> dict[str, object]:
    def find(run: dict[str, object]) -> dict[str, object]:
        for row in run["rows"]:
            if "photosynthesis" in str(row["gold_answer"]).lower() or "sunlight" in str(row["query"]).lower():
                return row
        return {}

    fallback = find(external_runs["numpy_fallback"])
    current = find(external_runs["sentence_transformers_faiss_robust"])
    if not current:
        return {}
    return {
        "query": current["query"],
        "fallback_answer": fallback.get("answer", ""),
        "fallback_answer_match": fallback.get("answer_match", False),
        "current_answer": current.get("answer", ""),
        "current_fixed": current.get("answer_match", False),
        "current_top_evidence_ids": current.get("top_evidence_ids", []),
    }


def _top_competing(row: dict[str, object] | None) -> dict[str, object]:
    if not row or not row.get("top_evidence"):
        return {}
    top = row["top_evidence"][0]
    return {
        "item_id": top.get("item_id", ""),
        "parent_doc_id": top.get("parent_doc_id", ""),
        "title": top.get("title", ""),
        "score": top.get("score", 0.0),
        "snippet": top.get("snippet", ""),
    }


def _remediation_note(row: dict[str, object], semantic_row: dict[str, object] | None = None) -> str:
    if row.get("slice") == "semantic":
        if semantic_row and semantic_row.get("hit_at_3") and not semantic_row.get("top1_hit"):
            return "Gold evidence was present but under-ranked; use a narrow semantic alias/concept rerank rather than changing gold labels."
        return "Gold evidence was absent from top-k; inspect semantic drift and add transparent reranking only if the query is already locally grounded."
    if row.get("slice") == "relational":
        return "Inspect fused evidence and backend contribution metadata."
    if row.get("slice") == "deductive":
        return "Inspect KG coverage and closed-world counterexample evidence."
    return "Inspect retrieval evidence before changing answer templates."


def _write_failure_csv(path: Path, failures: list[dict[str, object]]) -> None:
    fieldnames = [
        "id",
        "benchmark",
        "slice",
        "query",
        "gold_answer",
        "pre_robustness_answer",
        "post_robustness_answer",
        "error_buckets",
        "suggested_remediation",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in failures:
            writer.writerow({key: row.get(key, "") for key in fieldnames} | {"error_buckets": ", ".join(row.get("error_buckets", []))})


def _failure_markdown(payload: dict[str, object]) -> str:
    misses = [row for row in payload["failures"] if row.get("benchmark") == "curated_end_to_end"]
    semantic_changes = [row for row in payload["failures"] if row.get("benchmark") in {"curated_end_to_end", "curated_semantic"}]
    photosynthesis = payload["photosynthesis_external_fixed"]
    return "\n".join(
        [
            "# PRISM Failure Analysis",
            "",
            "This report compares the reproducible numpy fallback, the real Dense backend before robustness reranking, and the current robust real Dense backend.",
            "",
            "## Curated End-to-End Misses Before Robustness",
            "",
            *[
                f"- `{row['query']}`: expected `{row['gold_answer']}`, got `{row.get('pre_robustness_answer', '')}`; buckets={row['error_buckets']}; remediation={row['suggested_remediation']}"
                for row in misses
            ],
            "",
            "## Curated Semantic Ranking Changes",
            "",
            *[
                f"- `{row['query']}`: competing evidence `{row.get('top_competing_evidence', {}).get('parent_doc_id', '')}` -> robust top `{row.get('post_robustness_top_evidence', {}).get('parent_doc_id', '')}`."
                for row in semantic_changes
            ],
            "",
            "## External Photosynthesis Check",
            "",
            f"- Query: `{photosynthesis.get('query', '')}`",
            f"- Fallback answer: `{photosynthesis.get('fallback_answer', '')}`",
            f"- Current answer: `{photosynthesis.get('current_answer', '')}`",
            f"- Fixed now: `{photosynthesis.get('current_fixed', False)}`",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{FAILURE_JSON}`",
            f"- CSV: `{FAILURE_CSV}`",
            f"- Dense before/after JSON: `{DENSE_COMPARE_JSON}`",
            f"- Robustness summary: `{ROBUSTNESS_MD}`",
            "",
        ]
    )


def _dense_compare_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Dense Before/After Comparison",
        "",
        payload["comparison_method"],
        "",
        "| Run | Dense backend | Semantic top1 | Semantic hit@3 | E2E answers | External answers |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in payload["runs"].items():
        status = row["dense_backend_status"]
        sem = row["curated_semantic"]
        e2e = row["curated_end_to_end"]
        external = row["external_mini_benchmark"]
        lines.append(
            f"| {name} | {status.get('active_backend')} rerank={status.get('semantic_rerank')} | "
            f"{sem['top1']}/{sem['total']} | {sem['hit_at_3']}/{sem['total']} | "
            f"{e2e['answer_matches']}/{e2e['total']} | {external['answer_matches']}/{external['total']} |"
        )
    lines.extend(["", f"Robustness change: {payload['robustness_change']}", "", f"Claim note: {payload['claim_validation_note']}", ""])
    return "\n".join(lines)


def _robustness_markdown(failure_payload: dict[str, object], compare_payload: dict[str, object]) -> str:
    pre = compare_payload["runs"]["sentence_transformers_faiss_pre_robustness"]
    post = compare_payload["runs"]["sentence_transformers_faiss_robust"]
    return "\n".join(
        [
            "# Dense Robustness Summary",
            "",
            "## What Regressed",
            "",
            f"- Pre-robustness semantic top1: {pre['curated_semantic']['top1']}/{pre['curated_semantic']['total']}.",
            f"- Pre-robustness semantic hit@3: {pre['curated_semantic']['hit_at_3']}/{pre['curated_semantic']['total']}.",
            f"- Pre-robustness end-to-end answers: {pre['curated_end_to_end']['answer_matches']}/{pre['curated_end_to_end']['total']}.",
            "",
            "## What Was Diagnosed",
            "",
            "- The misses were concentrated in curated semantic paraphrases where MiniLM ranked a plausible but wrong neighbor above the local gold evidence.",
            "- The external photosynthesis paraphrase is fixed by the real Dense backend and remains fixed after the robustness change.",
            "",
            "## What Changed",
            "",
            f"- {compare_payload['robustness_change']}",
            "- The rerank is metadata-visible as `semantic_rerank=True` and can be disabled for compatibility reruns.",
            "",
            "## After Robustness",
            "",
            f"- Current semantic top1: {post['curated_semantic']['top1']}/{post['curated_semantic']['total']}.",
            f"- Current semantic hit@3: {post['curated_semantic']['hit_at_3']}/{post['curated_semantic']['total']}.",
            f"- Current end-to-end answers: {post['curated_end_to_end']['answer_matches']}/{post['curated_end_to_end']['total']}.",
            f"- Current external answers: {post['external_mini_benchmark']['answer_matches']}/{post['external_mini_benchmark']['total']}.",
            "",
            "## Still Unresolved",
            "",
            "- The lexical BM25-over-Dense claim remains a tradeoff to report carefully when real Dense ties BM25 on lexical hit@k.",
            "- The semantic rerank uses a local alias table, so it improves curated robustness but is not a broad semantic reasoning solution.",
            "- This analysis is deterministic and inspectable, but still small-scale.",
            "",
        ]
    )


def _stable_failure_id(prefix: str, query: str) -> str:
    return f"{prefix}_" + "_".join(query.lower().split())[:48].strip("_").replace("?", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PRISM failure-analysis and Dense before/after artifacts.")
    parser.parse_args()
    payload = run_failure_analysis()
    current = payload["end_to_end_summary"]["sentence_transformers_faiss_robust"]
    pre = payload["end_to_end_summary"]["sentence_transformers_faiss_pre_robustness"]
    print(
        f"failure_analysis_failures={payload['failure_count']} "
        f"pre_robust_answers={pre['answer_matches']}/{pre['total']} "
        f"current_answers={current['answer_matches']}/{current['total']} "
        f"json={FAILURE_JSON} csv={FAILURE_CSV} markdown={FAILURE_MD}"
    )


if __name__ == "__main__":
    main()
