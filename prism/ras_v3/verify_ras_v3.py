from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

from prism.adversarial.benchmark_builder import build_adversarial_benchmark
from prism.adversarial.loaders import AdversarialItem, load_adversarial_benchmark
from prism.adversarial.verify_adversarial import _build_retrievers as build_hard_retrievers
from prism.adversarial.verify_adversarial import _load_hard_context_documents, _train_classifier
from prism.analysis.evaluation import BACKENDS, answer_matches_gold, build_retrievers, load_combined_benchmark
from prism.answering.generator import synthesize_answer
from prism.calibration.dev_tuning import tune_calibrator_on_adversarial_dev
from prism.calibration.route_calibrator import CalibratorConfig, RouteCalibrator
from prism.calibration.topk_rescue import rescue_topk_evidence
from prism.calibration.verify_calibrated_router import (
    EvalRecord,
    _counter_breakdown,
    _expanded_evidence_ids,
    _record_evidence_hit,
)
from prism.external_benchmarks.loaders import load_external_mini_benchmark
from prism.generalization.loaders import load_generalization_benchmark
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.open_corpus.verify_open_corpus import SMOKE_JSON, verify_open_corpus
from prism.public_corpus.loaders import load_public_benchmark
from prism.public_graph.build_public_graph import load_public_structure_triples
from prism.ras.compute_ras import route_query
from prism.ras.route_improvement import route_query_v2
from prism.ras_v3.explain import explanation_payload, feature_weight_summary
from prism.ras_v3.features import extract_features
from prism.ras_v3.model import RASV3Model, RASV3TrainingExample
from prism.ras_v3.scoring import DEFAULT_MODEL_PATH, route_query_v3
from prism.router_baselines.rule_router import keyword_rule_route
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_jsonl_documents, read_jsonl_triples, write_json

EVAL_DIR = Path("data/eval")
HUMAN_DIR = Path("data/human_eval")
JSON_PATH = EVAL_DIR / "ras_v3_eval.json"
CSV_PATH = EVAL_DIR / "ras_v3_eval.csv"
MARKDOWN_PATH = EVAL_DIR / "ras_v3_eval_summary.md"
WEIGHTS_PATH = EVAL_DIR / "ras_v3_feature_weights.json"
EXPLANATIONS_PATH = EVAL_DIR / "ras_v3_explanations.json"
CASE_STUDIES_PATH = EVAL_DIR / "ras_v3_case_studies.md"
PAPER_PATH = EVAL_DIR / "ras_v3_for_paper.md"
HUMAN_JSON_PATH = HUMAN_DIR / "ras_v3_vs_human_summary.json"
HUMAN_MD_PATH = HUMAN_DIR / "ras_v3_vs_human_summary.md"
COMPARISON_PLOT = EVAL_DIR / "ras_v3_router_comparison.png"
TAG_PLOT = EVAL_DIR / "ras_v3_adversarial_tag_breakdown.png"
WEIGHTS_PLOT = EVAL_DIR / "ras_v3_feature_weights.png"

SYSTEMS = (
    "computed_ras",
    "computed_ras_v2",
    "ras_v3",
    "calibrated_rescue",
    "classifier_router",
    "keyword_router",
    "always_bm25",
    "always_dense",
    "always_kg",
    "always_hybrid",
)


@dataclass(frozen=True, slots=True)
class DatasetBundle:
    name: str
    kind: str
    records: list[EvalRecord]
    retrievers: dict[str, object]
    source_type: str


@dataclass(frozen=True, slots=True)
class RoutePrediction:
    route: str
    rationale: str
    margin: float = 0.0
    route_scores: dict[str, float] | None = None
    calibrated: bool = False


def verify_ras_v3(seed: int = 67) -> dict[str, object]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    build_adversarial_benchmark()
    clean_documents, clean_triples, clean_retrievers = _load_clean_context()
    hard_documents = _load_hard_context_documents()
    hard_triples = load_public_structure_triples("mixed_public_demo")
    hard_retrievers = build_hard_retrievers(hard_documents, hard_triples)

    adversarial_items = load_adversarial_benchmark()
    adversarial_dev = [item for item in adversarial_items if item.split == "dev"]
    adversarial_test = [item for item in adversarial_items if item.split == "test"]
    training_examples = _training_examples(adversarial_dev)
    model = RASV3Model.fit(training_examples, seed=seed)
    model.save(DEFAULT_MODEL_PATH)
    classifier = _train_classifier(seed)
    tuning_payload = tune_calibrator_on_adversarial_dev(adversarial_dev, classifier)
    calibrator = RouteCalibrator(CalibratorConfig(**tuning_payload["selected_config"]), classifier=classifier)

    datasets = [
        DatasetBundle("curated", "curated", _curated_records(), clean_retrievers, "curated"),
        DatasetBundle("external_mini", "external", _external_records(), clean_retrievers, "external"),
        DatasetBundle("generalization_v2_test", "generalization_v2", _generalization_records("test"), clean_retrievers, "generalization_v2_test"),
        DatasetBundle("public_raw_test", "public_raw", _public_records("test"), hard_retrievers, "public_raw_test"),
        DatasetBundle("adversarial_dev", "adversarial", [_adversarial_record(item) for item in adversarial_dev], hard_retrievers, "adversarial_dev"),
        DatasetBundle("adversarial_test", "adversarial", [_adversarial_record(item) for item in adversarial_test], hard_retrievers, "adversarial_test"),
    ]
    systems = {
        dataset.name: {
            system: _evaluate_system(system, dataset, model, classifier, calibrator)
            for system in SYSTEMS
        }
        for dataset in datasets
    }
    open_smoke = _open_corpus_smoke_reference()
    explanations = _explanations(model, systems["adversarial_test"])
    human = _human_alignment(model)
    weights_payload = {
        "model_version": model.model_version,
        "training_protocol": model.training_protocol,
        "feature_names": model.feature_names,
        "top_weights_by_route": feature_weight_summary(model.weights, top_n=12),
        "weights": model.weights,
        "intercepts": model.intercepts,
    }
    promotion = _promotion_decision(systems, human)
    payload = {
        "seed": seed,
        "production_router": "computed_ras",
        "ras_v3_status": promotion["decision"],
        "protocol": _protocol(model, training_examples),
        "datasets": {dataset.name: {"kind": dataset.kind, "total": len(dataset.records)} for dataset in datasets},
        "systems": systems,
        "open_corpus_smoke_reference": open_smoke,
        "feature_weights_path": str(WEIGHTS_PATH),
        "case_studies_path": str(CASE_STUDIES_PATH),
        "explanations_path": str(EXPLANATIONS_PATH),
        "human_alignment_path": str(HUMAN_JSON_PATH),
        "promotion_decision": promotion,
        "baseline_takeaways": _baseline_takeaways(systems),
        "artifacts": {
            "json": str(JSON_PATH),
            "csv": str(CSV_PATH),
            "markdown": str(MARKDOWN_PATH),
            "feature_weights": str(WEIGHTS_PATH),
            "explanations": str(EXPLANATIONS_PATH),
            "case_studies": str(CASE_STUDIES_PATH),
            "paper": str(PAPER_PATH),
            "human_json": str(HUMAN_JSON_PATH),
            "human_markdown": str(HUMAN_MD_PATH),
            "comparison_plot": str(COMPARISON_PLOT),
            "tag_plot": str(TAG_PLOT),
            "weights_plot": str(WEIGHTS_PLOT),
            "model": str(DEFAULT_MODEL_PATH),
        },
    }
    write_json(JSON_PATH, payload)
    write_json(WEIGHTS_PATH, weights_payload)
    write_json(EXPLANATIONS_PATH, explanations)
    write_json(HUMAN_JSON_PATH, human)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    CASE_STUDIES_PATH.write_text(_case_studies_markdown(explanations), encoding="utf-8")
    HUMAN_MD_PATH.write_text(_human_markdown(human), encoding="utf-8")
    PAPER_PATH.write_text(_paper_markdown(payload, human), encoding="utf-8")
    _plot_comparison(payload, COMPARISON_PLOT)
    _plot_adversarial_tags(payload, TAG_PLOT)
    _plot_weights(weights_payload, WEIGHTS_PLOT)
    return payload


def _load_clean_context() -> tuple[list[Document], list[Triple], dict[str, object]]:
    corpus_path = build_corpus()
    kg_path = build_kg(corpus_path=str(corpus_path))
    documents = read_jsonl_documents(corpus_path)
    triples = read_jsonl_triples(kg_path)
    return documents, triples, build_retrievers(documents, triples)


def _training_examples(adversarial_dev: list[AdversarialItem]) -> list[RASV3TrainingExample]:
    examples: list[RASV3TrainingExample] = []
    for row in load_combined_benchmark():
        examples.append(RASV3TrainingExample(str(row["query"]), str(row["gold_route"]), source_type="curated_train"))
    for item in load_generalization_benchmark(split="dev"):
        examples.append(RASV3TrainingExample(item.query, item.route_family, source_type="generalization_v2_dev"))
    for item in load_public_benchmark(split="dev"):
        examples.append(RASV3TrainingExample(item.query, item.route_family, source_type="public_raw_dev"))
    for item in adversarial_dev:
        examples.append(
            RASV3TrainingExample(
                item.query,
                item.intended_route_family,
                source_type="adversarial_dev",
                topk_rescue_opportunity="top-k" in item.notes.lower() or "top-k" in " ".join(item.ambiguity_tags),
            )
        )
    return examples


def _curated_records() -> list[EvalRecord]:
    records: list[EvalRecord] = []
    for row in load_combined_benchmark():
        records.append(
            EvalRecord(
                id=f"curated_{len(records):03d}",
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
            ambiguity_tags=[item.tag] if item.tag else [],
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


def _evaluate_system(
    system: str,
    dataset: DatasetBundle,
    model: RASV3Model,
    classifier,
    calibrator: RouteCalibrator,
) -> dict[str, object]:
    counters = Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0)
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    per_tag = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    predicted_distribution: Counter[str] = Counter()
    confusion: Counter[str] = Counter()
    margin_values: list[float] = []
    rows: list[dict[str, object]] = []
    for record in dataset.records:
        prediction = _select_route(system, record, dataset.source_type, model, classifier, calibrator)
        backend = prediction.route
        top_k = 5 if backend == "hybrid" else 3
        decision = route_query(record.query)
        evidence = dataset.retrievers[backend].retrieve(record.query, top_k=top_k)
        rescue_metadata = {"applied": False}
        if system == "calibrated_rescue":
            evidence, rescue_metadata = rescue_topk_evidence(record.query, evidence, backend)
        answer = synthesize_answer(record.query, decision.features, decision.ras_scores, backend, evidence)
        evidence_ids = _expanded_evidence_ids(evidence)
        evidence_ok = _record_evidence_hit(record, evidence, evidence_ids, dataset.kind)
        top1_ok = _record_evidence_hit(record, evidence[:1], _expanded_evidence_ids(evidence[:1]), dataset.kind)
        answer_ok = answer_matches_gold(answer.final_answer, record.gold_answer)
        route_ok = backend == record.family
        counters["total"] += 1
        counters["route_correct"] += int(route_ok)
        counters["answer_correct"] += int(answer_ok)
        counters["evidence_hits"] += int(evidence_ok)
        counters["top1_hits"] += int(top1_ok)
        _update_counter(per_family[record.family], route_ok, answer_ok, evidence_ok, top1_ok)
        for tag in record.ambiguity_tags or []:
            if tag:
                _update_counter(per_tag[tag], route_ok, answer_ok, evidence_ok, top1_ok)
        predicted_distribution[backend] += 1
        confusion[f"{record.family}->{backend}"] += 1
        margin_values.append(prediction.margin)
        rows.append(
            {
                "id": record.id,
                "query": record.query,
                "split": record.split,
                "family": record.family,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "answer": answer.final_answer,
                "gold_answer": record.gold_answer,
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "top1_evidence_hit": top1_ok,
                "top1_topk_gap": evidence_ok and not top1_ok,
                "evidence_ids": [item.item_id for item in evidence],
                "ambiguity_tags": record.ambiguity_tags or [],
                "route_margin": prediction.margin,
                "route_scores": prediction.route_scores or {},
                "route_rationale": prediction.rationale,
                "calibrated": prediction.calibrated,
                "topk_rescue": rescue_metadata,
            }
        )
    total = counters["total"]
    return {
        "system": system,
        "total": total,
        "route_accuracy": counters["route_correct"] / total if total else 0.0,
        "answer_accuracy": counters["answer_correct"] / total if total else 0.0,
        "evidence_hit_at_k": counters["evidence_hits"] / total if total else 0.0,
        "top1_evidence_hit": counters["top1_hits"] / total if total else 0.0,
        "route_correct": counters["route_correct"],
        "answer_correct": counters["answer_correct"],
        "evidence_hits": counters["evidence_hits"],
        "top1_hits": counters["top1_hits"],
        "per_family": _counter_breakdown(per_family),
        "per_ambiguity_tag": _counter_breakdown(per_tag),
        "predicted_distribution": dict(predicted_distribution),
        "confusion": dict(confusion),
        "mean_route_margin": sum(margin_values) / len(margin_values) if margin_values else 0.0,
        "low_margin_count": sum(1 for margin in margin_values if margin < 0.35),
        "results": rows,
    }


def _select_route(
    system: str,
    record: EvalRecord,
    source_type: str,
    model: RASV3Model,
    classifier,
    calibrator: RouteCalibrator,
) -> RoutePrediction:
    query = record.query
    if system == "computed_ras":
        decision = route_query(query)
        scores = {backend: -float(score) for backend, score in decision.ras_scores.items()}
        return RoutePrediction(decision.selected_backend, "Minimum computed RAS penalty.", _margin(scores), scores)
    if system == "computed_ras_v2":
        decision = route_query_v2(query, source_type_hint=source_type)
        return RoutePrediction(decision.selected_backend, decision.rationale, decision.margin, {backend: -value for backend, value in decision.ras_scores.items()})
    if system == "ras_v3":
        decision = route_query_v3(
            query,
            model=model,
            source_type=source_type,
            topk_rescue_opportunity=bool(record.ambiguity_tags and "evidence_present_topk_not_top1" in record.ambiguity_tags),
        )
        return RoutePrediction(decision.selected_backend, decision.rationale, decision.margin, decision.route_scores)
    if system == "calibrated_rescue":
        decision = calibrator.predict(query)
        return RoutePrediction(decision.selected_backend, decision.rationale, float(decision.confidence_score), decision.ras_scores, decision.calibrated)
    if system == "classifier_router":
        prediction = classifier.predict(query)
        scores = prediction.scores
        return RoutePrediction(prediction.route, prediction.rationale, _margin(scores), scores)
    if system == "keyword_router":
        prediction = keyword_rule_route(query)
        return RoutePrediction(prediction.route, prediction.rationale, _margin(prediction.scores), prediction.scores)
    if system.startswith("always_"):
        return RoutePrediction(system.removeprefix("always_"), "Fixed-backend baseline.", 0.0, {})
    raise ValueError(f"Unsupported RAS V3 comparison system: {system}")


def _update_counter(counter: Counter[str], route_ok: bool, answer_ok: bool, evidence_ok: bool, top1_ok: bool) -> None:
    counter["total"] += 1
    counter["route_correct"] += int(route_ok)
    counter["answer_correct"] += int(answer_ok)
    counter["evidence_hits"] += int(evidence_ok)
    counter["top1_hits"] += int(top1_ok)


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted((float(value) for value in scores.values()), reverse=True)
    if len(ordered) < 2:
        return 0.0
    return ordered[0] - ordered[1]


def _protocol(model: RASV3Model, examples: list[RASV3TrainingExample]) -> dict[str, object]:
    return {
        "model": model.training_protocol,
        "fit_data": "curated 80-query benchmark, generalization_v2 dev, public raw dev, and adversarial dev.",
        "held_out_reporting": "external mini, generalization_v2 test, public raw test, adversarial test, and open-corpus smoke are reporting/sanity layers.",
        "not_used_for_tuning": ["adversarial_test", "generalization_v2_test", "public_raw_test", "external_mini", "human_annotations"],
        "training_example_count": len(examples),
        "production_policy": "computed_ras remains production unless RAS_V3 passes strict promotion guardrails.",
    }


def _open_corpus_smoke_reference() -> dict[str, object]:
    if not SMOKE_JSON.exists():
        verify_open_corpus()
    try:
        payload = json.loads(SMOKE_JSON.read_text(encoding="utf-8"))
        return {
            "status": payload.get("status"),
            "total": payload.get("smoke", {}).get("total"),
            "route_accuracy": payload.get("smoke", {}).get("route_accuracy"),
            "answer_accuracy": payload.get("smoke", {}).get("answer_accuracy"),
            "evidence_hit_at_k": payload.get("smoke", {}).get("evidence_hit_at_k"),
            "note": "Open-corpus smoke is used as a functional workspace sanity check, not as RAS_V3 fitting data.",
        }
    except (OSError, json.JSONDecodeError):
        return {"status": "missing", "note": "Open-corpus smoke artifact was unavailable."}


def _explanations(model: RASV3Model, adversarial_test: dict[str, object]) -> dict[str, object]:
    changed = [
        row
        for row in adversarial_test["ras_v3"]["results"]
        if row["predicted_backend"]
        != next(
            base["predicted_backend"]
            for base in adversarial_test["computed_ras"]["results"]
            if base["id"] == row["id"]
        )
    ]
    selected_rows = changed[:5] or adversarial_test["ras_v3"]["results"][:5]
    cases = []
    for row in selected_rows:
        decision = route_query_v3(
            str(row["query"]),
            model=model,
            source_type="adversarial_test",
            topk_rescue_opportunity=bool(row.get("top1_topk_gap")),
        )
        payload = explanation_payload(decision)
        payload.update(
            {
                "id": row["id"],
                "gold_route": row["family"],
                "answer_correct": row["answer_correct"],
                "route_correct": row["route_correct"],
                "ambiguity_tags": row.get("ambiguity_tags", []),
            }
        )
        cases.append(payload)
    return {
        "model_version": model.model_version,
        "case_selection": "adversarial-test examples where RAS_V3 changed computed RAS, falling back to representative RAS_V3 cases.",
        "case_count": len(cases),
        "cases": cases,
    }


def _human_alignment(model: RASV3Model) -> dict[str, object]:
    packet_path = HUMAN_DIR / "comparative_packet.json"
    annotation_dir = HUMAN_DIR / "comparative_annotations"
    if not packet_path.exists() or not annotation_dir.exists():
        return {"status": "missing_human_artifacts", "note": "Comparative packet or annotations are missing."}
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    items = {item["comparative_item_id"]: item for item in packet.get("items", [])}
    votes_by_item: dict[str, Counter[str]] = defaultdict(Counter)
    for path in sorted(annotation_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                item_id = row.get("comparative_item_id", "")
                preference = row.get("overall_preference", "")
                if item_id and preference:
                    votes_by_item[item_id][preference] += 1
    evaluated = 0
    computed_matches = 0
    ras_v3_matches = 0
    recovered_b_preferences = 0
    adversarial_evaluated = 0
    adversarial_ras_v3_matches = 0
    rows = []
    for item_id, votes in sorted(votes_by_item.items()):
        item = items.get(item_id)
        if not item:
            continue
        winner = _majority_vote(votes)
        if winner not in {"A", "B"}:
            continue
        preferred_system = item["system_a"] if winner == "A" else item["system_b"]
        preferred_route = str(preferred_system.get("route") or preferred_system.get("selected_backend"))
        computed_route = route_query(str(item["query"])).selected_backend
        ras_v3_route = route_query_v3(str(item["query"]), model=model, source_type=str(item["source_benchmark"])).selected_backend
        computed_ok = computed_route == preferred_route
        ras_v3_ok = ras_v3_route == preferred_route
        evaluated += 1
        computed_matches += int(computed_ok)
        ras_v3_matches += int(ras_v3_ok)
        recovered_b_preferences += int(winner == "B" and ras_v3_ok and not computed_ok)
        if item.get("source_benchmark") == "adversarial":
            adversarial_evaluated += 1
            adversarial_ras_v3_matches += int(ras_v3_ok)
        rows.append(
            {
                "comparative_item_id": item_id,
                "query": item["query"],
                "source_benchmark": item["source_benchmark"],
                "route_family": item["route_family"],
                "system_pair": f"{item['system_a_label']}_vs_{item['system_b_label']}",
                "majority_vote": winner,
                "vote_counts": dict(votes),
                "preferred_route": preferred_route,
                "computed_ras_route": computed_route,
                "ras_v3_route": ras_v3_route,
                "computed_matches_human_preferred_route": computed_ok,
                "ras_v3_matches_human_preferred_route": ras_v3_ok,
            }
        )
    return {
        "status": "evaluated",
        "packet_size": len(items),
        "majority_preference_items_evaluated": evaluated,
        "computed_ras_human_preferred_route_alignment": computed_matches / evaluated if evaluated else 0.0,
        "ras_v3_human_preferred_route_alignment": ras_v3_matches / evaluated if evaluated else 0.0,
        "alignment_delta_ras_v3_minus_computed": (ras_v3_matches - computed_matches) / evaluated if evaluated else 0.0,
        "ras_v3_recovered_b_preferences": recovered_b_preferences,
        "adversarial_items_evaluated": adversarial_evaluated,
        "adversarial_ras_v3_alignment": adversarial_ras_v3_matches / adversarial_evaluated if adversarial_evaluated else 0.0,
        "automatic_correct_humanly_weak_note": "RAS_V3 outputs were not newly annotated; this artifact compares route choices to existing comparative preferences rather than claiming direct human ratings of RAS_V3 answers.",
        "rows": rows,
    }


def _majority_vote(votes: Counter[str]) -> str:
    if not votes:
        return ""
    ranked = votes.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "Tie"
    return ranked[0][0]


def _promotion_decision(systems: dict[str, dict[str, dict[str, object]]], human: dict[str, object]) -> dict[str, object]:
    adv_all = systems["adversarial_test"]
    ras = adv_all["computed_ras"]
    ras_v2 = adv_all["computed_ras_v2"]
    ras_v3 = adv_all["ras_v3"]
    calibrated = adv_all["calibrated_rescue"]
    answer_delta = float(ras_v3["answer_accuracy"]) - float(ras["answer_accuracy"])
    route_delta = float(ras_v3["route_accuracy"]) - float(ras["route_accuracy"])
    no_regressions = all(
        float(systems[name]["ras_v3"]["answer_accuracy"]) + 1e-9 >= float(systems[name]["computed_ras"]["answer_accuracy"]) - 0.01
        for name in ("curated", "external_mini", "generalization_v2_test", "public_raw_test")
    )
    human_delta = float(human.get("alignment_delta_ras_v3_minus_computed", 0.0)) if human.get("status") == "evaluated" else 0.0
    materially_better = answer_delta >= 0.03 and float(ras_v3["answer_accuracy"]) >= float(ras_v2["answer_accuracy"])
    beats_calibrated = float(ras_v3["answer_accuracy"]) >= float(calibrated["answer_accuracy"])
    promoted = materially_better and no_regressions and human_delta >= -0.01 and beats_calibrated
    return {
        "decision": "promote_to_production" if promoted else "keep_analysis_only",
        "production_router_after_evaluation": "ras_v3" if promoted else "computed_ras",
        "adversarial_answer_delta_vs_computed": answer_delta,
        "adversarial_route_delta_vs_computed": route_delta,
        "no_material_regression_on_guardrails": no_regressions,
        "human_alignment_delta_vs_computed": human_delta,
        "beats_calibrated_rescue_on_adversarial_test": beats_calibrated,
        "rationale": (
            "RAS_V3 passes all promotion guardrails."
            if promoted
            else "RAS_V3 remains analysis-only because at least one strict guardrail was not met."
        ),
        "guardrails": {
            "adversarial_overall_material_improvement": materially_better,
            "held_out_no_regression": no_regressions,
            "human_alignment_not_worse": human_delta >= -0.01,
            "interpretable_linear_model": True,
            "beats_calibrated_rescue": beats_calibrated,
        },
    }


def _baseline_takeaways(systems: dict[str, dict[str, dict[str, object]]]) -> list[str]:
    lines = []
    for dataset in ("adversarial_test", "curated", "external_mini", "generalization_v2_test", "public_raw_test"):
        rows = systems[dataset]
        strongest = max(rows, key=lambda name: float(rows[name]["answer_accuracy"]))
        lines.append(
            f"{dataset}: strongest answer system is {strongest} at {rows[strongest]['answer_accuracy']:.3f}; "
            f"RAS_V3={rows['ras_v3']['answer_accuracy']:.3f}, computed RAS={rows['computed_ras']['answer_accuracy']:.3f}."
        )
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
                "mean_route_margin",
                "low_margin_count",
            ],
        )
        writer.writeheader()
        for dataset, rows in payload["systems"].items():
            for system, row in rows.items():
                writer.writerow(
                    {
                        "dataset": dataset,
                        "system": system,
                        "total": row["total"],
                        "route_accuracy": row["route_accuracy"],
                        "answer_accuracy": row["answer_accuracy"],
                        "evidence_hit_at_k": row["evidence_hit_at_k"],
                        "top1_evidence_hit": row["top1_evidence_hit"],
                        "mean_route_margin": row["mean_route_margin"],
                        "low_margin_count": row["low_margin_count"],
                    }
                )


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# RAS V3 Evaluation Summary",
        "",
        f"Production router after evaluation: `{payload['promotion_decision']['production_router_after_evaluation']}`.",
        f"Decision: `{payload['promotion_decision']['decision']}`.",
        "",
        "## Protocol",
        "",
        f"- Fit data: {payload['protocol']['fit_data']}",
        f"- Held-out reporting: {payload['protocol']['held_out_reporting']}",
        f"- Not used for tuning: {', '.join(payload['protocol']['not_used_for_tuning'])}",
        "",
        "## Adversarial Test Comparison",
        "",
        "| System | Route accuracy | Answer accuracy | Evidence hit@k | Mean margin |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for system in SYSTEMS:
        row = payload["systems"]["adversarial_test"][system]
        lines.append(
            f"| {system} | {row['route_accuracy']:.3f} | {row['answer_accuracy']:.3f} | "
            f"{row['evidence_hit_at_k']:.3f} | {row['mean_route_margin']:.3f} |"
        )
    lines.extend(["", "## Guardrail Datasets", ""])
    for dataset in ("curated", "external_mini", "generalization_v2_test", "public_raw_test"):
        computed = payload["systems"][dataset]["computed_ras"]
        ras_v3 = payload["systems"][dataset]["ras_v3"]
        lines.append(
            f"- {dataset}: computed RAS answer={computed['answer_accuracy']:.3f}, "
            f"RAS_V3 answer={ras_v3['answer_accuracy']:.3f}, delta={ras_v3['answer_accuracy'] - computed['answer_accuracy']:+.3f}."
        )
    lines.extend(["", "## Baseline Takeaways", "", *[f"- {line}" for line in payload["baseline_takeaways"]]])
    lines.extend(
        [
            "",
            "## Promotion Decision",
            "",
            f"- {payload['promotion_decision']['rationale']}",
            f"- Adversarial answer delta vs computed RAS: {payload['promotion_decision']['adversarial_answer_delta_vs_computed']:+.3f}",
            f"- Human alignment delta vs computed RAS: {payload['promotion_decision']['human_alignment_delta_vs_computed']:+.3f}",
            f"- Beats calibrated rescue: {payload['promotion_decision']['beats_calibrated_rescue_on_adversarial_test']}",
            "",
            "## Artifacts",
            "",
            *[f"- {key}: `{value}`" for key, value in payload["artifacts"].items()],
            "",
        ]
    )
    return "\n".join(lines)


def _case_studies_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# RAS V3 Case Studies",
        "",
        f"Case selection: {payload['case_selection']}",
        "",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"Query: {case['query']}",
                f"Gold route: `{case['gold_route']}`. RAS_V3 route: `{case['selected_backend']}`.",
                f"Route correct: `{case['route_correct']}`. Answer correct: `{case['answer_correct']}`.",
                f"Rationale: {case['rationale']}",
                "",
                "Top contributions:",
            ]
        )
        for contribution in case["top_selected_route_contributions"][:6]:
            lines.append(f"- `{contribution['feature']}`: {contribution['contribution']:+.3f}")
        lines.append("")
    return "\n".join(lines)


def _human_markdown(payload: dict[str, object]) -> str:
    lines = ["# RAS V3 Vs Human Comparative Preferences", ""]
    if payload.get("status") != "evaluated":
        lines.append(f"Status: `{payload.get('status')}`. {payload.get('note', '')}")
        return "\n".join(lines)
    lines.extend(
        [
            f"Comparative packet size: {payload['packet_size']}.",
            f"Majority-preference items evaluated: {payload['majority_preference_items_evaluated']}.",
            f"Computed RAS preferred-route alignment: {payload['computed_ras_human_preferred_route_alignment']:.3f}.",
            f"RAS_V3 preferred-route alignment: {payload['ras_v3_human_preferred_route_alignment']:.3f}.",
            f"Alignment delta: {payload['alignment_delta_ras_v3_minus_computed']:+.3f}.",
            f"RAS_V3 recovered B-preference route choices: {payload['ras_v3_recovered_b_preferences']}.",
            "",
            "## Scope Note",
            "",
            payload["automatic_correct_humanly_weak_note"],
            "",
            "## Examples",
            "",
        ]
    )
    for row in payload["rows"][:10]:
        lines.append(
            f"- `{row['comparative_item_id']}` {row['system_pair']}: preferred route `{row['preferred_route']}`, "
            f"computed `{row['computed_ras_route']}`, RAS_V3 `{row['ras_v3_route']}`."
        )
    return "\n".join(lines)


def _paper_markdown(payload: dict[str, object], human: dict[str, object]) -> str:
    promotion = payload["promotion_decision"]
    lines = [
        "# RAS V3 For Paper",
        "",
        "RAS_V3 formalizes PRISM routing as a feature-based linear adequacy model over BM25, Dense, KG, and Hybrid route families.",
        "",
        "## What Changed",
        "",
        "- Computed RAS uses a fixed penalty table over parsed query families.",
        "- RAS_V2 added narrow hard-case arbitration heuristics.",
        "- RAS_V3 exposes a route feature vector, learned route weights, per-route scores, margins, and per-feature contributions.",
        "",
        "## Training Protocol",
        "",
        f"- {payload['protocol']['fit_data']}",
        f"- Held-out reporting: {payload['protocol']['held_out_reporting']}",
        "- Human annotations are used only for post-hoc alignment analysis, not training.",
        "",
        "## Main Result",
        "",
        f"- Adversarial test computed RAS answer accuracy: {payload['systems']['adversarial_test']['computed_ras']['answer_accuracy']:.3f}.",
        f"- Adversarial test RAS_V3 answer accuracy: {payload['systems']['adversarial_test']['ras_v3']['answer_accuracy']:.3f}.",
        f"- Adversarial test calibrated rescue answer accuracy: {payload['systems']['adversarial_test']['calibrated_rescue']['answer_accuracy']:.3f}.",
        f"- Promotion decision: `{promotion['decision']}`.",
        "",
        "## Human Alignment",
        "",
    ]
    if human.get("status") == "evaluated":
        lines.extend(
            [
                f"- Computed RAS alignment with human-preferred route: {human['computed_ras_human_preferred_route_alignment']:.3f}.",
                f"- RAS_V3 alignment with human-preferred route: {human['ras_v3_human_preferred_route_alignment']:.3f}.",
                f"- Delta: {human['alignment_delta_ras_v3_minus_computed']:+.3f}.",
            ]
        )
    else:
        lines.append("- Human alignment could not be computed from current artifacts.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            promotion["rationale"],
            "RAS remains the central contribution because the model is still an explicit adequacy-scoring framework, not a black-box replacement.",
            "",
            "## Threats To Validity",
            "",
            "- RAS_V3 uses small local/dev training data.",
            "- Hard-case benchmarks include hand-constructed ambiguity cases.",
            "- Answer metrics remain normalized string matching.",
            "- Human alignment compares route choices to existing comparative preferences, not newly annotated RAS_V3 answers.",
            "- Calibrated rescue may still outperform pure route scoring because it changes evidence ordering after retrieval.",
            "",
        ]
    )
    return "\n".join(lines)


def _plot_comparison(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np

    systems = ["computed_ras", "computed_ras_v2", "ras_v3", "calibrated_rescue", "classifier_router", "keyword_router"]
    route_values = [payload["systems"]["adversarial_test"][system]["route_accuracy"] for system in systems]
    answer_values = [payload["systems"]["adversarial_test"][system]["answer_accuracy"] for system in systems]
    image = np.ones((260, 520, 3), dtype=float)
    baseline = 220
    group_gap = 78
    colors = ([0.18, 0.35, 0.58], [0.82, 0.48, 0.28])
    for index, (route_value, answer_value) in enumerate(zip(route_values, answer_values)):
        left = 22 + index * group_gap
        route_height = int(max(0.0, min(1.0, float(route_value))) * 185)
        answer_height = int(max(0.0, min(1.0, float(answer_value))) * 185)
        image[baseline - route_height : baseline, left : left + 24, :] = colors[0]
        image[baseline - answer_height : baseline, left + 28 : left + 52, :] = colors[1]
    image[baseline : baseline + 2, 10:510, :] = 0.2
    image[35:38, 10:510, :] = 0.85
    path.parent.mkdir(parents=True, exist_ok=True)
    mpimg.imsave(path, image)


def _plot_adversarial_tags(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np

    tags = list(payload["systems"]["adversarial_test"]["ras_v3"]["per_ambiguity_tag"].keys())[:10]
    ras_values = [payload["systems"]["adversarial_test"]["computed_ras"]["per_ambiguity_tag"].get(tag, {}).get("answer_accuracy", 0.0) for tag in tags]
    v3_values = [payload["systems"]["adversarial_test"]["ras_v3"]["per_ambiguity_tag"].get(tag, {}).get("answer_accuracy", 0.0) for tag in tags]
    image = np.ones((250, max(420, len(tags) * 58), 3), dtype=float)
    baseline = 215
    for index, (ras_value, v3_value) in enumerate(zip(ras_values, v3_values)):
        left = 18 + index * 58
        ras_height = int(max(0.0, min(1.0, float(ras_value))) * 175)
        v3_height = int(max(0.0, min(1.0, float(v3_value))) * 175)
        image[baseline - ras_height : baseline, left : left + 22, :] = [0.50, 0.50, 0.50]
        image[baseline - v3_height : baseline, left + 25 : left + 47, :] = [0.22, 0.48, 0.66]
    image[baseline : baseline + 2, 10:-10, :] = 0.2
    path.parent.mkdir(parents=True, exist_ok=True)
    mpimg.imsave(path, image)


def _plot_weights(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np

    rows = payload["top_weights_by_route"].get("dense", [])[:8]
    values = [row["weight"] for row in rows]
    max_abs = max([abs(float(value)) for value in values] + [1.0])
    image = np.ones((230, 420, 3), dtype=float)
    center = 210
    for index, value in enumerate(values):
        y0 = 18 + index * 25
        width = int(abs(float(value)) / max_abs * 170)
        if value >= 0:
            image[y0 : y0 + 16, center : center + width, :] = [0.24, 0.56, 0.34]
        else:
            image[y0 : y0 + 16, center - width : center, :] = [0.70, 0.30, 0.25]
    image[10:220, center : center + 2, :] = 0.15
    path.parent.mkdir(parents=True, exist_ok=True)
    mpimg.imsave(path, image)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and verify the interpretable RAS V3 routing experiment.")
    parser.add_argument("--seed", type=int, default=67)
    args = parser.parse_args()
    payload = verify_ras_v3(seed=args.seed)
    adv = payload["systems"]["adversarial_test"]
    print(
        "ras_v3 "
        f"decision={payload['promotion_decision']['decision']} "
        f"computed_answer={adv['computed_ras']['answer_accuracy']:.3f} "
        f"ras_v3_answer={adv['ras_v3']['answer_accuracy']:.3f} "
        f"calibrated_rescue_answer={adv['calibrated_rescue']['answer_accuracy']:.3f} "
        f"json={JSON_PATH} markdown={MARKDOWN_PATH}"
    )
    for line in payload["baseline_takeaways"]:
        print(line)


if __name__ == "__main__":
    main()
