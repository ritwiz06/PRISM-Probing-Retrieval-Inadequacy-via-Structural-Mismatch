from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from prism.adversarial.benchmark_builder import build_adversarial_benchmark
from prism.adversarial.failure_analysis import analyze_adversarial_failures
from prism.adversarial.loaders import AdversarialItem, load_adversarial_benchmark
from prism.adversarial.verify_adversarial import (
    _build_retrievers as build_hard_retrievers,
    _evidence_hit as adversarial_evidence_hit,
    _load_hard_context_documents,
    _payload_evidence,
    _train_classifier,
)
from prism.analysis.evaluation import (
    BACKENDS,
    answer_matches_gold,
    build_retrievers,
    evidence_id_set,
    load_combined_benchmark,
)
from prism.answering.generator import synthesize_answer
from prism.calibration.dev_tuning import tune_calibrator_on_adversarial_dev
from prism.calibration.route_calibrator import CalibratorConfig, RouteCalibrator
from prism.calibration.topk_rescue import rescue_topk_evidence
from prism.external_benchmarks.loaders import load_external_mini_benchmark
from prism.generalization.loaders import load_generalization_benchmark
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.public_corpus.loaders import load_public_benchmark
from prism.public_graph.build_public_graph import load_public_structure_triples
from prism.ras.compute_ras import route_query
from prism.router_baselines.classifier_router import ClassifierRouter
from prism.router_baselines.rule_router import RouterPrediction
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

EVAL_DIR = Path("data/eval")
JSON_PATH = EVAL_DIR / "calibrated_router.json"
CSV_PATH = EVAL_DIR / "calibrated_router.csv"
MARKDOWN_PATH = EVAL_DIR / "calibrated_router_summary.md"
FAILURE_DELTA_JSON_PATH = EVAL_DIR / "calibrated_failure_delta.json"
FAILURE_DELTA_MARKDOWN_PATH = EVAL_DIR / "calibrated_failure_delta_summary.md"
ADVERSARIAL_TEST_PLOT = EVAL_DIR / "calibrated_adversarial_test_comparison.png"
FAILURE_DELTA_PLOT = EVAL_DIR / "calibrated_failure_delta.png"

SYSTEMS = (
    "computed_ras",
    "computed_ras_calibrated",
    "computed_ras_topk_rescue",
    "computed_ras_calibrated_topk_rescue",
    "classifier_router",
    "always_bm25",
    "always_dense",
    "always_kg",
    "always_hybrid",
)


@dataclass(frozen=True, slots=True)
class EvalRecord:
    id: str
    query: str
    split: str
    family: str
    gold_answer: str
    gold_source_doc_ids: list[str]
    gold_triple_ids: list[str]
    gold_evidence_text: str = ""
    ambiguity_tags: list[str] | None = None


def verify_calibrated_router(seed: int = 53) -> dict[str, object]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    benchmark_path = build_adversarial_benchmark()
    adversarial_items = load_adversarial_benchmark(benchmark_path)
    adversarial_dev = [item for item in adversarial_items if item.split == "dev"]
    adversarial_test = [item for item in adversarial_items if item.split == "test"]
    classifier = _train_classifier(seed)
    tuning_payload = tune_calibrator_on_adversarial_dev(adversarial_dev, classifier)
    calibrator = RouteCalibrator(CalibratorConfig(**tuning_payload["selected_config"]), classifier=classifier)

    clean_documents, clean_triples, clean_retrievers = _load_clean_context()
    hard_documents = _load_hard_context_documents()
    hard_triples = load_public_structure_triples("mixed_public_demo")
    hard_retrievers = build_hard_retrievers(hard_documents, hard_triples)

    datasets = {
        "adversarial_dev": ([_adversarial_record(item) for item in adversarial_dev], hard_retrievers, "adversarial"),
        "adversarial_test": ([_adversarial_record(item) for item in adversarial_test], hard_retrievers, "adversarial"),
        "curated": (_curated_records(), clean_retrievers, "curated"),
        "external_mini": (_external_records(), clean_retrievers, "external"),
        "generalization_v2_test": (_generalization_records("test"), clean_retrievers, "generalization_v2"),
        "public_raw_test": (_public_records("test"), hard_retrievers, "public_raw"),
    }
    dataset_results = {
        dataset_name: {
            system: _evaluate_records(system, records, retrievers, classifier, calibrator, dataset_kind)
            for system in SYSTEMS
        }
        for dataset_name, (records, retrievers, dataset_kind) in datasets.items()
    }
    failure_delta = _failure_delta(
        dataset_results["adversarial_test"]["computed_ras"],
        dataset_results["adversarial_test"]["computed_ras_calibrated_topk_rescue"],
    )
    payload = {
        "seed": seed,
        "protocol": {
            "production_router": "computed_ras remains the production default.",
            "calibration": tuning_payload["protocol"],
            "held_out": "Adversarial test, curated, external, generalization_v2 test, and public raw test are evaluation-only sanity checks.",
            "topk_rescue": "Top-k rescue reorders retrieved evidence only; it does not fetch new evidence and does not use gold labels.",
        },
        "selected_calibrator": tuning_payload["selected_config"],
        "dev_tuning": tuning_payload,
        "datasets": {
            name: {"total": len(records), "kind": kind}
            for name, (records, _retrievers, kind) in datasets.items()
        },
        "systems": dataset_results,
        "failure_delta": failure_delta,
        "takeaways": _takeaways(dataset_results, failure_delta),
        "tradeoffs": _tradeoffs(dataset_results),
        "artifacts": {
            "json": str(JSON_PATH),
            "csv": str(CSV_PATH),
            "markdown": str(MARKDOWN_PATH),
            "failure_delta_json": str(FAILURE_DELTA_JSON_PATH),
            "failure_delta_markdown": str(FAILURE_DELTA_MARKDOWN_PATH),
            "adversarial_test_plot": str(ADVERSARIAL_TEST_PLOT),
            "failure_delta_plot": str(FAILURE_DELTA_PLOT),
        },
        "context": {
            "clean_documents": len(clean_documents),
            "clean_triples": len(clean_triples),
            "hard_documents": len(hard_documents),
            "hard_triples": len(hard_triples),
        },
    }
    write_json(JSON_PATH, payload)
    write_json(FAILURE_DELTA_JSON_PATH, failure_delta)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    FAILURE_DELTA_MARKDOWN_PATH.write_text(_failure_delta_markdown(failure_delta), encoding="utf-8")
    _plot_adversarial_test(payload, ADVERSARIAL_TEST_PLOT)
    _plot_failure_delta(failure_delta, FAILURE_DELTA_PLOT)
    return payload


def _load_clean_context() -> tuple[list[Document], list[Triple], dict[str, object]]:
    corpus_path = build_corpus()
    kg_path = build_kg(corpus_path=str(corpus_path))
    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    return documents, triples, build_retrievers(documents, triples)


def _adversarial_record(item: AdversarialItem) -> EvalRecord:
    return EvalRecord(
        id=item.id,
        query=item.query,
        split=item.split,
        family=item.intended_route_family,
        gold_answer=item.gold_answer,
        gold_source_doc_ids=item.gold_source_doc_ids,
        gold_triple_ids=item.gold_triple_ids,
        gold_evidence_text=item.gold_evidence_text,
        ambiguity_tags=list(item.ambiguity_tags),
    )


def _curated_records() -> list[EvalRecord]:
    records = []
    for row in load_combined_benchmark():
        records.append(
            EvalRecord(
                id=f"curated_{row['slice']}_{len(records):03d}",
                query=str(row["query"]),
                split="all",
                family=str(row["gold_route"]),
                gold_answer=str(row["gold_answer"]),
                gold_source_doc_ids=[str(value) for value in row.get("gold_evidence_ids", [])],
                gold_triple_ids=[],
                gold_evidence_text="",
                ambiguity_tags=[],
            )
        )
    return records


def _external_records() -> list[EvalRecord]:
    return [
        EvalRecord(
            id=item.id,
            query=item.query,
            split="all",
            family=item.route_family,
            gold_answer=item.gold_answer,
            gold_source_doc_ids=[],
            gold_triple_ids=[],
            gold_evidence_text=item.gold_evidence_text,
            ambiguity_tags=[],
        )
        for item in load_external_mini_benchmark()
    ]


def _generalization_records(split: str) -> list[EvalRecord]:
    return [
        EvalRecord(
            id=item.id,
            query=item.query,
            split=item.split,
            family=item.route_family,
            gold_answer=item.gold_answer,
            gold_source_doc_ids=[],
            gold_triple_ids=[],
            gold_evidence_text=item.gold_evidence_text,
            ambiguity_tags=[item.tag] if item.tag else [],
        )
        for item in load_generalization_benchmark(split=split)
    ]


def _public_records(split: str) -> list[EvalRecord]:
    return [
        EvalRecord(
            id=item.id,
            query=item.query,
            split=item.split,
            family=item.route_family,
            gold_answer=item.gold_answer,
            gold_source_doc_ids=item.gold_source_doc_ids,
            gold_triple_ids=[],
            gold_evidence_text=item.gold_evidence_text,
            ambiguity_tags=[],
        )
        for item in load_public_benchmark(split=split)
    ]


def _evaluate_records(
    system_name: str,
    records: list[EvalRecord],
    retrievers: dict[str, object],
    classifier: ClassifierRouter,
    calibrator: RouteCalibrator,
    dataset_kind: str,
) -> dict[str, object]:
    counters = Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0, overrides=0, rescue_applied=0)
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    per_tag = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    rows: list[dict[str, object]] = []
    for record in records:
        route_prediction = _select_route(system_name, record.query, classifier, calibrator)
        selected_backend = route_prediction.route
        top_k = 5 if selected_backend == "hybrid" else 3
        decision = route_query(record.query)
        evidence = retrievers[selected_backend].retrieve(record.query, top_k=top_k)
        rescue_metadata = {"applied": False}
        if "topk_rescue" in system_name:
            evidence, rescue_metadata = rescue_topk_evidence(record.query, evidence, selected_backend)
        answer = synthesize_answer(record.query, decision.features, decision.ras_scores, selected_backend, evidence)
        evidence_ids = _expanded_evidence_ids(evidence)
        evidence_ok = _record_evidence_hit(record, evidence, evidence_ids, dataset_kind)
        top1_ok = _record_evidence_hit(record, evidence[:1], _expanded_evidence_ids(evidence[:1]), dataset_kind)
        answer_ok = answer_matches_gold(answer.final_answer, record.gold_answer)
        route_ok = selected_backend == record.family
        counters["total"] += 1
        counters["route_correct"] += int(route_ok)
        counters["answer_correct"] += int(answer_ok)
        counters["evidence_hits"] += int(evidence_ok)
        counters["top1_hits"] += int(top1_ok)
        counters["overrides"] += int(route_prediction.calibrated)
        counters["rescue_applied"] += int(bool(rescue_metadata.get("applied")))
        _update_counter(per_family[record.family], route_ok, answer_ok, evidence_ok, top1_ok)
        for tag in record.ambiguity_tags or []:
            if tag:
                _update_counter(per_tag[tag], route_ok, answer_ok, evidence_ok, top1_ok)
        rows.append(
            {
                "id": record.id,
                "query": record.query,
                "split": record.split,
                "family": record.family,
                "predicted_backend": selected_backend,
                "route_correct": route_ok,
                "answer": answer.final_answer,
                "gold_answer": record.gold_answer,
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "top1_evidence_hit": top1_ok,
                "top1_topk_gap": evidence_ok and not top1_ok,
                "evidence_ids": [item.item_id for item in evidence],
                "gold_source_doc_ids": record.gold_source_doc_ids,
                "gold_triple_ids": record.gold_triple_ids,
                "ambiguity_tags": record.ambiguity_tags or [],
                "route_rationale": route_prediction.rationale,
                "calibrated": route_prediction.calibrated,
                "topk_rescue": rescue_metadata,
            }
        )
    total = counters["total"]
    return {
        "system": system_name,
        "total": total,
        "route_accuracy": counters["route_correct"] / total if total else 0.0,
        "answer_accuracy": counters["answer_correct"] / total if total else 0.0,
        "evidence_hit_at_k": counters["evidence_hits"] / total if total else 0.0,
        "top1_evidence_hit": counters["top1_hits"] / total if total else 0.0,
        "top1_topk_gap_rate": (counters["evidence_hits"] - counters["top1_hits"]) / total if total else 0.0,
        "route_correct": counters["route_correct"],
        "answer_correct": counters["answer_correct"],
        "evidence_hits": counters["evidence_hits"],
        "top1_hits": counters["top1_hits"],
        "override_count": counters["overrides"],
        "topk_rescue_applied_count": counters["rescue_applied"],
        "per_family": _counter_breakdown(per_family),
        "per_ambiguity_tag": _counter_breakdown(per_tag),
        "results": rows,
    }


def _select_route(
    system_name: str,
    query: str,
    classifier: ClassifierRouter,
    calibrator: RouteCalibrator,
) -> RouterPrediction | _CalibratedPrediction:
    if system_name in {"computed_ras", "computed_ras_topk_rescue"}:
        decision = route_query(query)
        return _CalibratedPrediction(decision.selected_backend, False, "Minimum computed RAS penalty.")
    if system_name in {"computed_ras_calibrated", "computed_ras_calibrated_topk_rescue"}:
        decision = calibrator.predict(query)
        return _CalibratedPrediction(decision.selected_backend, decision.calibrated, decision.rationale)
    if system_name == "classifier_router":
        pred = classifier.predict(query)
        return _CalibratedPrediction(pred.route, False, pred.rationale)
    if system_name.startswith("always_"):
        return _CalibratedPrediction(system_name.removeprefix("always_"), False, "Fixed-backend baseline.")
    raise ValueError(f"Unsupported calibrated-router system: {system_name}")


@dataclass(frozen=True, slots=True)
class _CalibratedPrediction:
    route: str
    calibrated: bool
    rationale: str


def _expanded_evidence_ids(evidence: list[RetrievedItem]) -> set[str]:
    ids = evidence_id_set(evidence)
    for item in evidence:
        for key in ("source_doc_id", "kg_source_doc_id", "parent_doc_id", "chunk_id", "triple_id", "path_id", "component_ids"):
            for part in str(item.metadata.get(key, "")).split(","):
                if part:
                    ids.add(part)
    return ids


def _record_evidence_hit(record: EvalRecord, evidence: list[RetrievedItem], evidence_ids: set[str], dataset_kind: str) -> bool:
    if dataset_kind == "adversarial":
        item = AdversarialItem(
            id=record.id,
            query=record.query,
            split=record.split,
            intended_route_family=record.family,
            difficulty="hard",
            ambiguity_tags=record.ambiguity_tags or [],
            gold_answer=record.gold_answer,
            gold_source_doc_ids=record.gold_source_doc_ids,
            gold_triple_ids=record.gold_triple_ids,
            gold_evidence_text=record.gold_evidence_text,
        )
        return adversarial_evidence_hit(item, evidence, evidence_ids)
    gold = set(record.gold_source_doc_ids) | set(record.gold_triple_ids)
    if gold:
        return bool(gold & evidence_ids)
    text = " ".join([entry.content for entry in evidence] + sorted(evidence_ids))
    return _token_overlap(record.gold_evidence_text or record.gold_answer, text) >= 0.35


def _token_overlap(gold: str, observed: str) -> float:
    import re

    stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "what", "which", "not"}
    gold_tokens = {token for token in re.findall(r"[a-z0-9._§:/-]+", gold.lower()) if token not in stopwords}
    observed_tokens = set(re.findall(r"[a-z0-9._§:/-]+", observed.lower()))
    return len(gold_tokens & observed_tokens) / len(gold_tokens) if gold_tokens else 0.0


def _update_counter(counter: Counter[str], route_ok: bool, answer_ok: bool, evidence_ok: bool, top1_ok: bool) -> None:
    counter["total"] += 1
    counter["route_correct"] += int(route_ok)
    counter["answer_correct"] += int(answer_ok)
    counter["evidence_hits"] += int(evidence_ok)
    counter["top1_hits"] += int(top1_ok)


def _counter_breakdown(counters: dict[str, Counter[str]]) -> dict[str, dict[str, object]]:
    return {
        name: {
            "total": counter["total"],
            "route_accuracy": counter["route_correct"] / counter["total"] if counter["total"] else 0.0,
            "answer_accuracy": counter["answer_correct"] / counter["total"] if counter["total"] else 0.0,
            "evidence_hit_at_k": counter["evidence_hits"] / counter["total"] if counter["total"] else 0.0,
            "top1_evidence_hit": counter["top1_hits"] / counter["total"] if counter["total"] else 0.0,
            "top1_topk_gap_rate": (counter["evidence_hits"] - counter["top1_hits"]) / counter["total"] if counter["total"] else 0.0,
            "route_correct": counter["route_correct"],
            "answer_correct": counter["answer_correct"],
            "evidence_hits": counter["evidence_hits"],
            "top1_hits": counter["top1_hits"],
        }
        for name, counter in sorted(counters.items())
    }


def _failure_delta(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    before_analysis = analyze_adversarial_failures()
    before_failures = [row for row in before_analysis["failure_rows"] if row["id"] in {item["id"] for item in before["results"]}]
    after_rows = {row["id"]: row for row in after["results"]}
    before_buckets = Counter(bucket for row in before_failures for bucket in row["buckets"])
    after_buckets: Counter[str] = Counter()
    fixed = 0
    regressed = 0
    changed: list[dict[str, object]] = []
    for row in before_failures:
        after_row = after_rows.get(row["id"])
        if not after_row:
            continue
        if after_row["answer_correct"] and not row["answer_correct"]:
            fixed += 1
        if row["answer_correct"] and not after_row["answer_correct"]:
            regressed += 1
        if not after_row["answer_correct"] or not after_row["route_correct"] or not after_row["top1_evidence_hit"]:
            for bucket in row["buckets"]:
                after_buckets[bucket] += 1
        changed.append(
            {
                "id": row["id"],
                "query": row["query"],
                "before_answer_correct": row["answer_correct"],
                "after_answer_correct": after_row["answer_correct"],
                "before_route_correct": row["route_correct"],
                "after_route_correct": after_row["route_correct"],
                "before_top1_evidence_hit": row["top1_evidence_hit"],
                "after_top1_evidence_hit": after_row["top1_evidence_hit"],
                "buckets": row["buckets"],
            }
        )
    bucket_rows = {
        bucket: {
            "before": before_buckets[bucket],
            "after": after_buckets.get(bucket, 0),
            "delta": after_buckets.get(bucket, 0) - before_buckets[bucket],
        }
        for bucket in sorted(before_buckets)
    }
    return {
        "scope": "adversarial_test",
        "before_system": before["system"],
        "after_system": after["system"],
        "before_answer_accuracy": before["answer_accuracy"],
        "after_answer_accuracy": after["answer_accuracy"],
        "before_route_accuracy": before["route_accuracy"],
        "after_route_accuracy": after["route_accuracy"],
        "fixed_failures": fixed,
        "regressed_failures": regressed,
        "bucket_delta": bucket_rows,
        "examples": changed,
        "note": "Before buckets come from adversarial failure-analysis rules; after counts reuse those bucket labels for still-unfixed examples.",
    }


def _takeaways(dataset_results: dict[str, dict[str, dict[str, object]]], failure_delta: dict[str, object]) -> list[str]:
    adv_test = dataset_results["adversarial_test"]
    normal = adv_test["computed_ras"]
    calibrated = adv_test["computed_ras_calibrated"]
    rescue = adv_test["computed_ras_topk_rescue"]
    combined = adv_test["computed_ras_calibrated_topk_rescue"]
    strongest_fixed = max(
        (name for name in adv_test if name.startswith("always_")),
        key=lambda name: float(adv_test[name]["answer_accuracy"]),
    )
    return [
        f"Adversarial test normal computed RAS answer accuracy {normal['answer_accuracy']:.3f}.",
        f"Calibrated-only answer accuracy {calibrated['answer_accuracy']:.3f}.",
        f"Top-k rescue-only answer accuracy {rescue['answer_accuracy']:.3f}.",
        f"Calibrated+rescue answer accuracy {combined['answer_accuracy']:.3f}.",
        f"Strongest fixed backend on adversarial test is {strongest_fixed} at {adv_test[strongest_fixed]['answer_accuracy']:.3f}.",
        f"Failure delta fixed {failure_delta['fixed_failures']} prior failures and regressed {failure_delta['regressed_failures']}.",
    ]


def _tradeoffs(dataset_results: dict[str, dict[str, dict[str, object]]]) -> list[str]:
    lines: list[str] = []
    for dataset in ("curated", "external_mini", "generalization_v2_test", "public_raw_test"):
        normal = dataset_results[dataset]["computed_ras"]
        combined = dataset_results[dataset]["computed_ras_calibrated_topk_rescue"]
        delta = float(combined["answer_accuracy"]) - float(normal["answer_accuracy"])
        direction = "improved" if delta > 0 else "dropped" if delta < 0 else "stayed flat"
        lines.append(f"{dataset}: calibrated+rescue {direction} by {delta:+.3f} answer accuracy versus normal RAS.")
    lines.append("Calibration and rescue remain optional analysis modes; production computed RAS stays unchanged.")
    return lines


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "dataset",
                "system",
                "total",
                "route_accuracy",
                "answer_accuracy",
                "evidence_hit_at_k",
                "top1_evidence_hit",
                "top1_topk_gap_rate",
                "override_count",
                "topk_rescue_applied_count",
            ],
        )
        writer.writeheader()
        for dataset, systems in payload["systems"].items():
            for system, row in systems.items():
                writer.writerow(
                    {
                        "dataset": dataset,
                        "system": system,
                        "total": row["total"],
                        "route_accuracy": row["route_accuracy"],
                        "answer_accuracy": row["answer_accuracy"],
                        "evidence_hit_at_k": row["evidence_hit_at_k"],
                        "top1_evidence_hit": row["top1_evidence_hit"],
                        "top1_topk_gap_rate": row["top1_topk_gap_rate"],
                        "override_count": row["override_count"],
                        "topk_rescue_applied_count": row["topk_rescue_applied_count"],
                    }
                )


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Calibrated Router And Top-k Rescue Evaluation",
        "",
        "This is an optional analysis layer. Computed RAS remains the production router by default.",
        "",
        "## Protocol",
        "",
        f"- {payload['protocol']['calibration']}",
        f"- {payload['protocol']['topk_rescue']}",
        f"- {payload['protocol']['held_out']}",
        "",
        "## Selected Calibrator",
        "",
        f"- `{payload['selected_calibrator']['name']}` with config `{payload['selected_calibrator']}`.",
        "",
        "## Adversarial Test Comparison",
        "",
        "| System | Route accuracy | Answer accuracy | Evidence hit@k | Top-1 evidence hit | Overrides | Rescues |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for system in SYSTEMS:
        row = payload["systems"]["adversarial_test"][system]
        lines.append(
            f"| {system} | {row['route_accuracy']:.3f} | {row['answer_accuracy']:.3f} | {row['evidence_hit_at_k']:.3f} | "
            f"{row['top1_evidence_hit']:.3f} | {row['override_count']} | {row['topk_rescue_applied_count']} |"
        )
    lines.extend(["", "## Cross-Benchmark Sanity Checks", ""])
    for dataset in ("curated", "external_mini", "generalization_v2_test", "public_raw_test"):
        normal = payload["systems"][dataset]["computed_ras"]
        combined = payload["systems"][dataset]["computed_ras_calibrated_topk_rescue"]
        lines.append(
            f"- {dataset}: normal answer={normal['answer_accuracy']:.3f}, calibrated+rescue answer={combined['answer_accuracy']:.3f}, "
            f"delta={combined['answer_accuracy'] - normal['answer_accuracy']:+.3f}."
        )
    lines.extend(["", "## Per-Ambiguity Tag On Adversarial Test", ""])
    for tag, row in payload["systems"]["adversarial_test"]["computed_ras_calibrated_topk_rescue"]["per_ambiguity_tag"].items():
        lines.append(f"- {tag}: answer={row['answer_accuracy']:.3f}, route={row['route_accuracy']:.3f}, top1={row['top1_evidence_hit']:.3f}.")
    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            *[f"- {item}" for item in payload["takeaways"]],
            "",
            "## Tradeoffs",
            "",
            *[f"- {item}" for item in payload["tradeoffs"]],
            "",
            "## Artifacts",
            "",
            *[f"- {key}: `{value}`" for key, value in payload["artifacts"].items()],
            "",
        ]
    )
    return "\n".join(lines)


def _failure_delta_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Calibrated Failure Delta",
        "",
        f"Scope: `{payload['scope']}`.",
        f"Before: `{payload['before_system']}` answer={payload['before_answer_accuracy']:.3f}, route={payload['before_route_accuracy']:.3f}.",
        f"After: `{payload['after_system']}` answer={payload['after_answer_accuracy']:.3f}, route={payload['after_route_accuracy']:.3f}.",
        f"Fixed prior failures: {payload['fixed_failures']}.",
        f"Regressed prior failures: {payload['regressed_failures']}.",
        "",
        "## Bucket Delta",
        "",
        "| Bucket | Before | After | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for bucket, row in payload["bucket_delta"].items():
        lines.append(f"| {bucket} | {row['before']} | {row['after']} | {row['delta']:+d} |")
    lines.extend(["", "## Note", "", f"- {payload['note']}", ""])
    return "\n".join(lines)


def _plot_adversarial_test(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np

    systems = [
        "computed_ras",
        "computed_ras_calibrated",
        "computed_ras_topk_rescue",
        "computed_ras_calibrated_topk_rescue",
        "classifier_router",
        "always_dense",
    ]
    values = [payload["systems"]["adversarial_test"][system]["answer_accuracy"] for system in systems]
    image = np.ones((220, 420, 3), dtype=float)
    colors = np.array([[0.20, 0.35, 0.58], [0.27, 0.55, 0.68], [0.39, 0.67, 0.45], [0.80, 0.48, 0.25], [0.55, 0.38, 0.65], [0.45, 0.45, 0.45]])
    bar_width = 48
    gap = 18
    baseline = 200
    for index, value in enumerate(values):
        left = 18 + index * (bar_width + gap)
        height = int(max(0.0, min(1.0, float(value))) * 175)
        image[baseline - height : baseline, left : left + bar_width, :] = colors[index]
    image[25:28, 10:410, :] = 0.85
    path.parent.mkdir(parents=True, exist_ok=True)
    mpimg.imsave(path, image)


def _plot_failure_delta(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np

    buckets = list(payload["bucket_delta"].keys())
    before = [payload["bucket_delta"][bucket]["before"] for bucket in buckets]
    after = [payload["bucket_delta"][bucket]["after"] for bucket in buckets]
    max_value = max(before + after + [1])
    image = np.ones((240, max(360, len(buckets) * 58), 3), dtype=float)
    baseline = 215
    group_width = 42
    for index, (before_value, after_value) in enumerate(zip(before, after)):
        left = 14 + index * 58
        before_height = int((before_value / max_value) * 175)
        after_height = int((after_value / max_value) * 175)
        image[baseline - before_height : baseline, left : left + group_width // 2, :] = [0.65, 0.25, 0.25]
        image[baseline - after_height : baseline, left + group_width // 2 : left + group_width, :] = [0.25, 0.55, 0.35]
    image[35:38, 10:-10, :] = 0.85
    path.parent.mkdir(parents=True, exist_ok=True)
    mpimg.imsave(path, image)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify optional calibrated route and top-k rescue layer.")
    parser.add_argument("--seed", type=int, default=53)
    args = parser.parse_args()
    payload = verify_calibrated_router(seed=args.seed)
    adv = payload["systems"]["adversarial_test"]
    normal = adv["computed_ras"]
    combined = adv["computed_ras_calibrated_topk_rescue"]
    print(
        "calibrated_router "
        f"adversarial_test_normal_answer={normal['answer_accuracy']:.3f} "
        f"calibrated_rescue_answer={combined['answer_accuracy']:.3f} "
        f"normal_route={normal['route_accuracy']:.3f} "
        f"calibrated_rescue_route={combined['route_accuracy']:.3f} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
