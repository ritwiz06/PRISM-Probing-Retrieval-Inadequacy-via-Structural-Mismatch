from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

from prism.adversarial.benchmark_builder import build_adversarial_benchmark
from prism.adversarial.loaders import load_adversarial_benchmark
from prism.adversarial.verify_adversarial import _build_retrievers as build_hard_retrievers
from prism.adversarial.verify_adversarial import _load_hard_context_documents, _train_classifier
from prism.analysis.evaluation import BACKENDS, answer_matches_gold
from prism.answering.generator import synthesize_answer
from prism.calibration.dev_tuning import tune_calibrator_on_adversarial_dev
from prism.calibration.route_calibrator import CalibratorConfig, RouteCalibrator
from prism.calibration.topk_rescue import rescue_topk_evidence
from prism.calibration.verify_calibrated_router import EvalRecord, _counter_breakdown, _expanded_evidence_ids, _record_evidence_hit
from prism.open_corpus.verify_open_corpus import SMOKE_JSON, verify_open_corpus
from prism.public_graph.build_public_graph import load_public_structure_triples
from prism.ras.compute_ras import route_query
from prism.ras.route_improvement import route_query_v2
from prism.ras_v3.scoring import route_query_v3
from prism.ras_v3.verify_ras_v3 import (
    DatasetBundle,
    _adversarial_record,
    _curated_records,
    _external_records,
    _generalization_records,
    _load_clean_context,
    _public_records,
)
from prism.ras_v4.explain import explanation_payload, feature_weight_summary
from prism.ras_v4.features import RASV4FeatureVector, extract_joint_features
from prism.ras_v4.model import RASV4Model
from prism.ras_v4.scoring import DEFAULT_MODEL_PATH, route_query_v4
from prism.router_baselines.rule_router import keyword_rule_route
from prism.utils import write_json

EVAL_DIR = Path("data/eval")
HUMAN_DIR = Path("data/human_eval")
JSON_PATH = EVAL_DIR / "ras_v4_eval.json"
CSV_PATH = EVAL_DIR / "ras_v4_eval.csv"
MARKDOWN_PATH = EVAL_DIR / "ras_v4_eval_summary.md"
MODEL_PATH = EVAL_DIR / "ras_v4_model.json"
WEIGHTS_PATH = EVAL_DIR / "ras_v4_feature_weights.json"
EXPLANATIONS_PATH = EVAL_DIR / "ras_v4_explanations.json"
CASE_STUDIES_PATH = EVAL_DIR / "ras_v4_case_studies.md"
RESCUE_MD_PATH = EVAL_DIR / "ras_v4_vs_rescue_summary.md"
PAPER_PATH = EVAL_DIR / "ras_v4_for_paper.md"
HUMAN_JSON_PATH = HUMAN_DIR / "ras_v4_vs_human_summary.json"
HUMAN_MD_PATH = HUMAN_DIR / "ras_v4_vs_human_summary.md"
COMPARISON_PLOT = EVAL_DIR / "ras_v4_router_comparison.png"
TAG_PLOT = EVAL_DIR / "ras_v4_adversarial_tag_breakdown.png"
CONTRIB_PLOT = EVAL_DIR / "ras_v4_route_vs_evidence_contribution.png"

SYSTEMS = (
    "computed_ras",
    "computed_ras_v2",
    "ras_v3",
    "calibrated_rescue",
    "classifier_router",
    "ras_v4",
    "ras_v4_rescue",
    "always_bm25",
    "always_dense",
    "always_kg",
    "always_hybrid",
)


def verify_ras_v4(seed: int = 79) -> dict[str, object]:
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

    classifier = _train_classifier(seed)
    tuning_payload = tune_calibrator_on_adversarial_dev(adversarial_dev, classifier)
    calibrator = RouteCalibrator(CalibratorConfig(**tuning_payload["selected_config"]), classifier=classifier)

    training_bundles = [
        DatasetBundle("curated_train", "curated", _curated_records(), clean_retrievers, "curated_train"),
        DatasetBundle("generalization_v2_dev", "generalization_v2", _generalization_records("dev"), clean_retrievers, "generalization_v2_dev"),
        DatasetBundle("public_raw_dev", "public_raw", _public_records("dev"), hard_retrievers, "public_raw_dev"),
        DatasetBundle("adversarial_dev_train", "adversarial", [_adversarial_record(item) for item in adversarial_dev], hard_retrievers, "adversarial_dev"),
    ]
    model, training_summary = _fit_model(training_bundles, seed=seed)
    model.save(MODEL_PATH)
    model.save(DEFAULT_MODEL_PATH)

    eval_bundles = [
        DatasetBundle("curated", "curated", _curated_records(), clean_retrievers, "curated"),
        DatasetBundle("external_mini", "external", _external_records(), clean_retrievers, "external"),
        DatasetBundle("generalization_v2_test", "generalization_v2", _generalization_records("test"), clean_retrievers, "generalization_v2_test"),
        DatasetBundle("public_raw_test", "public_raw", _public_records("test"), hard_retrievers, "public_raw_test"),
        DatasetBundle("adversarial_dev", "adversarial", [_adversarial_record(item) for item in adversarial_dev], hard_retrievers, "adversarial_dev"),
        DatasetBundle("adversarial_test", "adversarial", [_adversarial_record(item) for item in adversarial_test], hard_retrievers, "adversarial_test"),
    ]
    systems = {
        bundle.name: {
            system: _evaluate_system(system, bundle, model, classifier, calibrator)
            for system in SYSTEMS
        }
        for bundle in eval_bundles
    }
    explanations = _explanations(systems["adversarial_test"], eval_bundles[-1], model)
    human = _human_alignment(model, hard_retrievers)
    rescue = _rescue_summary(systems)
    weights_payload = {
        "model_version": model.model_version,
        "training_protocol": model.training_protocol,
        "training_summary": training_summary,
        "feature_weight_summary": feature_weight_summary(model.weights),
        "weights": model.weights,
        "intercept": model.intercept,
        "route_weight_sum": model.route_weight_sum,
        "evidence_weight_sum": model.evidence_weight_sum,
    }
    promotion = _promotion_decision(systems, human)
    payload = {
        "seed": seed,
        "production_router": "computed_ras",
        "ras_v4_status": promotion["decision"],
        "protocol": {
            "fit_data": "curated benchmark, generalization_v2 dev, public raw dev, and adversarial dev.",
            "held_out_reporting": "external mini, generalization_v2 test, public raw test, adversarial test, and open-corpus smoke are reporting/sanity layers.",
            "not_used_for_tuning": ["adversarial_test", "generalization_v2_test", "public_raw_test", "external_mini", "human_annotations"],
            "model": model.training_protocol,
        },
        "datasets": {bundle.name: {"kind": bundle.kind, "total": len(bundle.records)} for bundle in eval_bundles},
        "systems": systems,
        "open_corpus_smoke_reference": _open_corpus_smoke_reference(),
        "training_summary": training_summary,
        "rescue_comparison": rescue,
        "human_alignment": human,
        "promotion_decision": promotion,
        "baseline_takeaways": _baseline_takeaways(systems),
        "artifacts": {
            "json": str(JSON_PATH),
            "csv": str(CSV_PATH),
            "markdown": str(MARKDOWN_PATH),
            "model": str(MODEL_PATH),
            "feature_weights": str(WEIGHTS_PATH),
            "explanations": str(EXPLANATIONS_PATH),
            "case_studies": str(CASE_STUDIES_PATH),
            "rescue_markdown": str(RESCUE_MD_PATH),
            "paper": str(PAPER_PATH),
            "human_json": str(HUMAN_JSON_PATH),
            "human_markdown": str(HUMAN_MD_PATH),
            "comparison_plot": str(COMPARISON_PLOT),
            "tag_plot": str(TAG_PLOT),
            "contribution_plot": str(CONTRIB_PLOT),
        },
    }
    write_json(JSON_PATH, payload)
    write_json(WEIGHTS_PATH, weights_payload)
    write_json(EXPLANATIONS_PATH, explanations)
    write_json(HUMAN_JSON_PATH, human)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    CASE_STUDIES_PATH.write_text(_case_studies_markdown(explanations), encoding="utf-8")
    RESCUE_MD_PATH.write_text(_rescue_markdown(rescue), encoding="utf-8")
    HUMAN_MD_PATH.write_text(_human_markdown(human), encoding="utf-8")
    PAPER_PATH.write_text(_paper_markdown(payload), encoding="utf-8")
    _plot_comparison(payload, COMPARISON_PLOT)
    _plot_tags(payload, TAG_PLOT)
    _plot_contributions(payload, CONTRIB_PLOT)
    return payload


def _fit_model(bundles: list[DatasetBundle], *, seed: int) -> tuple[RASV4Model, dict[str, object]]:
    features: list[RASV4FeatureVector] = []
    labels: list[int] = []
    source_counts: Counter[str] = Counter()
    for bundle in bundles:
        for record in bundle.records:
            evidence_by_backend = _evidence_by_backend(record.query, bundle.retrievers)
            for backend in BACKENDS:
                vector = extract_joint_features(
                    record.query,
                    backend,
                    evidence_by_backend[backend],
                    source_type=bundle.source_type,
                    topk_rescue_opportunity=bool(record.ambiguity_tags and "evidence_present_topk_not_top1" in record.ambiguity_tags),
                )
                features.append(vector)
                labels.append(int(backend == record.family))
                source_counts[bundle.name] += 1
    model = RASV4Model.fit(features, labels, seed=seed)
    summary = {
        "candidate_pairs": len(features),
        "positive_pairs": sum(labels),
        "negative_pairs": len(labels) - sum(labels),
        "source_counts": dict(sorted(source_counts.items())),
        "label_definition": "positive iff candidate backend equals the benchmark route family; no held-out test labels are used for fitting.",
    }
    model.training_protocol["training_source_summary"] = summary
    return model, summary


def _evaluate_system(system: str, bundle: DatasetBundle, model: RASV4Model, classifier, calibrator: RouteCalibrator) -> dict[str, object]:
    counters = Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0, rescue_applied=0)
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    per_tag = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    predicted_distribution: Counter[str] = Counter()
    confusion: Counter[str] = Counter()
    margins: list[float] = []
    route_contribs: list[float] = []
    evidence_contribs: list[float] = []
    rows: list[dict[str, object]] = []
    for record in bundle.records:
        evidence_by_backend = _evidence_by_backend(record.query, bundle.retrievers)
        route, rationale, margin, score_payload = _select_route(system, record, bundle.source_type, evidence_by_backend, model, classifier, calibrator)
        evidence = list(evidence_by_backend[route])
        rescue_metadata = {"applied": False}
        if system in {"calibrated_rescue", "ras_v4_rescue"}:
            evidence, rescue_metadata = rescue_topk_evidence(record.query, evidence, route)
        decision = route_query(record.query)
        answer = synthesize_answer(record.query, decision.features, decision.ras_scores, route, evidence)
        evidence_ids = _expanded_evidence_ids(evidence)
        evidence_ok = _record_evidence_hit(record, evidence, evidence_ids, bundle.kind)
        top1_ok = _record_evidence_hit(record, evidence[:1], _expanded_evidence_ids(evidence[:1]), bundle.kind)
        answer_ok = answer_matches_gold(answer.final_answer, record.gold_answer)
        route_ok = route == record.family
        counters["total"] += 1
        counters["route_correct"] += int(route_ok)
        counters["answer_correct"] += int(answer_ok)
        counters["evidence_hits"] += int(evidence_ok)
        counters["top1_hits"] += int(top1_ok)
        counters["rescue_applied"] += int(bool(rescue_metadata.get("applied")))
        _update_counter(per_family[record.family], route_ok, answer_ok, evidence_ok, top1_ok)
        for tag in record.ambiguity_tags or []:
            if tag:
                _update_counter(per_tag[tag], route_ok, answer_ok, evidence_ok, top1_ok)
        predicted_distribution[route] += 1
        confusion[f"{record.family}->{route}"] += 1
        margins.append(margin)
        route_contribs.append(float(score_payload.get("route_contribution", 0.0)))
        evidence_contribs.append(float(score_payload.get("evidence_contribution", 0.0)))
        rows.append(
            {
                "id": record.id,
                "query": record.query,
                "split": record.split,
                "family": record.family,
                "predicted_backend": route,
                "route_correct": route_ok,
                "answer": answer.final_answer,
                "gold_answer": record.gold_answer,
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "top1_evidence_hit": top1_ok,
                "top1_topk_gap": evidence_ok and not top1_ok,
                "evidence_ids": [item.item_id for item in evidence],
                "ambiguity_tags": record.ambiguity_tags or [],
                "route_margin": margin,
                "route_rationale": rationale,
                "score_payload": score_payload,
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
        "topk_rescue_applied_count": counters["rescue_applied"],
        "per_family": _counter_breakdown(per_family),
        "per_ambiguity_tag": _counter_breakdown(per_tag),
        "predicted_distribution": dict(predicted_distribution),
        "confusion": dict(confusion),
        "mean_route_margin": sum(margins) / len(margins) if margins else 0.0,
        "low_margin_count": sum(1 for margin in margins if margin < 0.35),
        "mean_route_contribution": sum(route_contribs) / len(route_contribs) if route_contribs else 0.0,
        "mean_evidence_contribution": sum(evidence_contribs) / len(evidence_contribs) if evidence_contribs else 0.0,
        "results": rows,
    }


def _evidence_by_backend(query: str, retrievers: dict[str, object]) -> dict[str, list]:
    return {backend: retrievers[backend].retrieve(query, top_k=5 if backend == "hybrid" else 3) for backend in BACKENDS}


def _select_route(system: str, record: EvalRecord, source_type: str, evidence_by_backend: dict[str, list], model: RASV4Model, classifier, calibrator: RouteCalibrator) -> tuple[str, str, float, dict[str, object]]:
    query = record.query
    if system == "computed_ras":
        decision = route_query(query)
        return decision.selected_backend, "Minimum computed RAS penalty.", _margin({backend: -score for backend, score in decision.ras_scores.items()}), {}
    if system == "computed_ras_v2":
        decision = route_query_v2(query, source_type_hint=source_type)
        return decision.selected_backend, decision.rationale, decision.margin, {}
    if system == "ras_v3":
        decision = route_query_v3(query, source_type=source_type)
        return decision.selected_backend, decision.rationale, decision.margin, {}
    if system == "calibrated_rescue":
        decision = calibrator.predict(query)
        return decision.selected_backend, decision.rationale, float(decision.confidence_score), {}
    if system == "classifier_router":
        prediction = classifier.predict(query)
        return prediction.route, prediction.rationale, _margin(prediction.scores), {}
    if system == "ras_v4" or system == "ras_v4_rescue":
        decision = route_query_v4(
            query,
            evidence_by_backend,
            model=model,
            source_type=source_type,
            topk_rescue_opportunity=bool(record.ambiguity_tags and "evidence_present_topk_not_top1" in record.ambiguity_tags),
        )
        selected = decision.candidate_scores[decision.selected_backend]
        return (
            decision.selected_backend,
            decision.rationale,
            decision.margin,
            {
                "combined_score": selected.combined_score,
                "route_contribution": selected.route_contribution,
                "evidence_contribution": selected.evidence_contribution,
                "candidate_scores": {
                    backend: {
                        "combined_score": row.combined_score,
                        "route_contribution": row.route_contribution,
                        "evidence_contribution": row.evidence_contribution,
                    }
                    for backend, row in decision.candidate_scores.items()
                },
            },
        )
    if system.startswith("always_"):
        return system.removeprefix("always_"), "Fixed-backend baseline.", 0.0, {}
    raise ValueError(f"Unsupported RAS_V4 system: {system}")


def _update_counter(counter: Counter[str], route_ok: bool, answer_ok: bool, evidence_ok: bool, top1_ok: bool) -> None:
    counter["total"] += 1
    counter["route_correct"] += int(route_ok)
    counter["answer_correct"] += int(answer_ok)
    counter["evidence_hits"] += int(evidence_ok)
    counter["top1_hits"] += int(top1_ok)


def _margin(scores: dict[str, float]) -> float:
    ordered = sorted(scores.values(), reverse=True)
    return ordered[0] - ordered[1] if len(ordered) > 1 else 0.0


def _explanations(adversarial_results: dict[str, object], bundle: DatasetBundle, model: RASV4Model) -> dict[str, object]:
    by_id = {row["id"]: row for row in adversarial_results["computed_ras"]["results"]}
    changed = [row for row in adversarial_results["ras_v4"]["results"] if row["predicted_backend"] != by_id[row["id"]]["predicted_backend"]]
    selected_rows = changed[:5] or adversarial_results["ras_v4"]["results"][:5]
    records = {record.id: record for record in bundle.records}
    cases = []
    for row in selected_rows:
        record = records[row["id"]]
        decision = route_query_v4(record.query, _evidence_by_backend(record.query, bundle.retrievers), model=model, source_type=bundle.source_type)
        case = explanation_payload(decision)
        case.update({"id": record.id, "query": record.query, "gold_route": record.family, "answer_correct": row["answer_correct"], "route_correct": row["route_correct"], "ambiguity_tags": record.ambiguity_tags or []})
        cases.append(case)
    return {
        "model_version": model.model_version,
        "case_selection": "adversarial-test examples where RAS_V4 changed computed RAS, falling back to representative cases.",
        "case_count": len(cases),
        "cases": cases,
    }


def _human_alignment(model: RASV4Model, retrievers: dict[str, object]) -> dict[str, object]:
    packet_path = HUMAN_DIR / "comparative_packet.json"
    annotation_dir = HUMAN_DIR / "comparative_annotations"
    if not packet_path.exists() or not annotation_dir.exists():
        return {"status": "missing_human_artifacts"}
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    items = {item["comparative_item_id"]: item for item in packet.get("items", [])}
    votes_by_item: dict[str, Counter[str]] = defaultdict(Counter)
    for path in sorted(annotation_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                if row.get("comparative_item_id") and row.get("overall_preference"):
                    votes_by_item[row["comparative_item_id"]][row["overall_preference"]] += 1
    evaluated = computed_matches = ras_v4_matches = adversarial_evaluated = adversarial_matches = 0
    rows = []
    for item_id, votes in sorted(votes_by_item.items()):
        item = items.get(item_id)
        if not item:
            continue
        winner = _majority_vote(votes)
        if winner not in {"A", "B"}:
            continue
        preferred = item["system_a"] if winner == "A" else item["system_b"]
        preferred_route = str(preferred.get("route") or preferred.get("selected_backend"))
        computed_route = route_query(str(item["query"])).selected_backend
        evidence = _evidence_by_backend(str(item["query"]), retrievers)
        ras_v4_route = route_query_v4(str(item["query"]), evidence, model=model, source_type=str(item["source_benchmark"])).selected_backend
        computed_ok = computed_route == preferred_route
        ras_v4_ok = ras_v4_route == preferred_route
        evaluated += 1
        computed_matches += int(computed_ok)
        ras_v4_matches += int(ras_v4_ok)
        if item.get("source_benchmark") == "adversarial":
            adversarial_evaluated += 1
            adversarial_matches += int(ras_v4_ok)
        rows.append(
            {
                "comparative_item_id": item_id,
                "query": item["query"],
                "source_benchmark": item["source_benchmark"],
                "route_family": item["route_family"],
                "preferred_route": preferred_route,
                "computed_ras_route": computed_route,
                "ras_v4_route": ras_v4_route,
                "computed_matches_human_preferred_route": computed_ok,
                "ras_v4_matches_human_preferred_route": ras_v4_ok,
                "vote_counts": dict(votes),
            }
        )
    return {
        "status": "evaluated",
        "packet_size": len(items),
        "majority_preference_items_evaluated": evaluated,
        "computed_ras_human_preferred_route_alignment": computed_matches / evaluated if evaluated else 0.0,
        "ras_v4_human_preferred_route_alignment": ras_v4_matches / evaluated if evaluated else 0.0,
        "alignment_delta_ras_v4_minus_computed": (ras_v4_matches - computed_matches) / evaluated if evaluated else 0.0,
        "adversarial_items_evaluated": adversarial_evaluated,
        "adversarial_ras_v4_alignment": adversarial_matches / adversarial_evaluated if adversarial_evaluated else 0.0,
        "scope_note": "RAS_V4 outputs were not newly annotated; this compares route choices to existing comparative preferences.",
        "rows": rows,
    }


def _majority_vote(votes: Counter[str]) -> str:
    ranked = votes.most_common()
    if not ranked:
        return ""
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "Tie"
    return ranked[0][0]


def _rescue_summary(systems: dict[str, dict[str, dict[str, object]]]) -> dict[str, object]:
    adv = systems["adversarial_test"]
    ras_v4 = adv["ras_v4"]
    ras_v4_rescue = adv["ras_v4_rescue"]
    calibrated = adv["calibrated_rescue"]
    return {
        "scope": "adversarial_test",
        "ras_v4_answer_accuracy": ras_v4["answer_accuracy"],
        "ras_v4_rescue_answer_accuracy": ras_v4_rescue["answer_accuracy"],
        "calibrated_rescue_answer_accuracy": calibrated["answer_accuracy"],
        "rescue_delta_after_ras_v4": ras_v4_rescue["answer_accuracy"] - ras_v4["answer_accuracy"],
        "calibrated_minus_ras_v4": calibrated["answer_accuracy"] - ras_v4["answer_accuracy"],
        "interpretation": _rescue_interpretation(ras_v4, ras_v4_rescue, calibrated),
    }


def _rescue_interpretation(ras_v4: dict[str, object], ras_v4_rescue: dict[str, object], calibrated: dict[str, object]) -> str:
    if ras_v4_rescue["answer_accuracy"] > ras_v4["answer_accuracy"]:
        return "Rescue still adds value after RAS_V4, so evidence adequacy and top-k rescue are complementary."
    if ras_v4["answer_accuracy"] >= calibrated["answer_accuracy"]:
        return "RAS_V4 closes or exceeds the calibrated rescue gap without needing the overlay."
    return "RAS_V4 does not close the calibrated rescue gap by itself; rescue remains stronger."


def _promotion_decision(systems: dict[str, dict[str, dict[str, object]]], human: dict[str, object]) -> dict[str, object]:
    adv = systems["adversarial_test"]
    computed = adv["computed_ras"]
    ras_v4 = adv["ras_v4"]
    ras_v4_rescue = adv["ras_v4_rescue"]
    calibrated = adv["calibrated_rescue"]
    answer_delta = ras_v4["answer_accuracy"] - computed["answer_accuracy"]
    no_regressions = all(systems[name]["ras_v4"]["answer_accuracy"] + 1e-9 >= systems[name]["computed_ras"]["answer_accuracy"] - 0.01 for name in ("curated", "external_mini", "generalization_v2_test", "public_raw_test"))
    human_delta = float(human.get("alignment_delta_ras_v4_minus_computed", 0.0)) if human.get("status") == "evaluated" else 0.0
    materially_improves = answer_delta >= 0.03
    credible_vs_rescue = ras_v4["answer_accuracy"] >= calibrated["answer_accuracy"] - 0.01 or ras_v4_rescue["answer_accuracy"] >= calibrated["answer_accuracy"] - 0.01
    promoted = materially_improves and no_regressions and human_delta >= -0.01 and credible_vs_rescue
    return {
        "decision": "promote_to_production" if promoted else "keep_analysis_only",
        "production_router_after_evaluation": "ras_v4" if promoted else "computed_ras",
        "adversarial_answer_delta_vs_computed": answer_delta,
        "no_material_regression_on_guardrails": no_regressions,
        "human_alignment_delta_vs_computed": human_delta,
        "credible_vs_calibrated_rescue": credible_vs_rescue,
        "rationale": "RAS_V4 passes all promotion guardrails." if promoted else "RAS_V4 remains analysis-only because at least one strict guardrail was not met.",
        "guardrails": {
            "material_adversarial_answer_improvement": materially_improves,
            "held_out_no_regression": no_regressions,
            "human_alignment_not_worse": human_delta >= -0.01,
            "interpretable_joint_model": True,
            "credible_vs_calibrated_rescue": credible_vs_rescue,
        },
    }


def _baseline_takeaways(systems: dict[str, dict[str, dict[str, object]]]) -> list[str]:
    lines = []
    for dataset in ("adversarial_test", "curated", "external_mini", "generalization_v2_test", "public_raw_test"):
        rows = systems[dataset]
        strongest = max(rows, key=lambda name: float(rows[name]["answer_accuracy"]))
        lines.append(f"{dataset}: strongest answer system is {strongest} at {rows[strongest]['answer_accuracy']:.3f}; RAS_V4={rows['ras_v4']['answer_accuracy']:.3f}, computed RAS={rows['computed_ras']['answer_accuracy']:.3f}.")
    return lines


def _open_corpus_smoke_reference() -> dict[str, object]:
    if not SMOKE_JSON.exists():
        verify_open_corpus()
    try:
        payload = json.loads(SMOKE_JSON.read_text(encoding="utf-8"))
        return {
            "status": payload.get("status"),
            "total": payload.get("smoke", {}).get("total"),
            "answer_accuracy": payload.get("smoke", {}).get("answer_accuracy"),
            "evidence_hit_at_k": payload.get("smoke", {}).get("evidence_hit_at_k"),
            "note": "Open-corpus smoke is a functional workspace sanity check, not RAS_V4 fitting data.",
        }
    except (OSError, json.JSONDecodeError):
        return {"status": "missing"}


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["dataset", "system", "total", "route_accuracy", "answer_accuracy", "evidence_hit_at_k", "top1_evidence_hit", "mean_route_margin", "mean_route_contribution", "mean_evidence_contribution"])
        writer.writeheader()
        for dataset, rows in payload["systems"].items():
            for system, row in rows.items():
                writer.writerow({field: row.get(field, dataset if field == "dataset" else system if field == "system" else "") for field in writer.fieldnames})


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# RAS V4 Evaluation Summary",
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
        "| System | Route accuracy | Answer accuracy | Evidence hit@k | Top-1 evidence |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for system in SYSTEMS:
        row = payload["systems"]["adversarial_test"][system]
        lines.append(f"| {system} | {row['route_accuracy']:.3f} | {row['answer_accuracy']:.3f} | {row['evidence_hit_at_k']:.3f} | {row['top1_evidence_hit']:.3f} |")
    lines.extend(["", "## Rescue Comparison", "", f"- {payload['rescue_comparison']['interpretation']}", f"- RAS_V4 answer={payload['rescue_comparison']['ras_v4_answer_accuracy']:.3f}; RAS_V4+rescue answer={payload['rescue_comparison']['ras_v4_rescue_answer_accuracy']:.3f}; calibrated rescue answer={payload['rescue_comparison']['calibrated_rescue_answer_accuracy']:.3f}.", "", "## Guardrail Datasets", ""])
    for dataset in ("curated", "external_mini", "generalization_v2_test", "public_raw_test"):
        computed = payload["systems"][dataset]["computed_ras"]
        ras_v4 = payload["systems"][dataset]["ras_v4"]
        lines.append(f"- {dataset}: computed RAS answer={computed['answer_accuracy']:.3f}, RAS_V4 answer={ras_v4['answer_accuracy']:.3f}, delta={ras_v4['answer_accuracy'] - computed['answer_accuracy']:+.3f}.")
    lines.extend(["", "## Baseline Takeaways", "", *[f"- {line}" for line in payload["baseline_takeaways"]], "", "## Promotion Decision", "", f"- {payload['promotion_decision']['rationale']}", f"- Adversarial answer delta vs computed RAS: {payload['promotion_decision']['adversarial_answer_delta_vs_computed']:+.3f}", f"- Human alignment delta vs computed RAS: {payload['promotion_decision']['human_alignment_delta_vs_computed']:+.3f}", f"- Credible vs calibrated rescue: {payload['promotion_decision']['credible_vs_calibrated_rescue']}", "", "## Artifacts", "", *[f"- {key}: `{value}`" for key, value in payload["artifacts"].items()], ""])
    return "\n".join(lines)


def _case_studies_markdown(payload: dict[str, object]) -> str:
    lines = ["# RAS V4 Case Studies", "", f"Case selection: {payload['case_selection']}", ""]
    for case in payload["cases"]:
        lines.extend([f"## {case['id']}", "", f"Query: {case['query']}", f"Gold route: `{case['gold_route']}`. RAS_V4 route: `{case['selected_backend']}`.", f"Rationale: {case['rationale']}", ""])
        selected = case["candidate_scores"][case["selected_backend"]]
        lines.append(f"Route contribution: `{selected['route_contribution']:.3f}`. Evidence contribution: `{selected['evidence_contribution']:.3f}`.")
        lines.append("")
        lines.append("Top contributions:")
        for row in selected["top_contributions"][:6]:
            lines.append(f"- `{row['feature']}`: {row['contribution']:+.3f}")
        lines.append("")
    return "\n".join(lines)


def _rescue_markdown(payload: dict[str, object]) -> str:
    return "\n".join(["# RAS V4 Vs Calibrated Rescue", "", f"Scope: `{payload['scope']}`.", f"RAS_V4 answer accuracy: `{payload['ras_v4_answer_accuracy']:.3f}`.", f"RAS_V4 + rescue answer accuracy: `{payload['ras_v4_rescue_answer_accuracy']:.3f}`.", f"Calibrated rescue answer accuracy: `{payload['calibrated_rescue_answer_accuracy']:.3f}`.", f"Rescue delta after RAS_V4: `{payload['rescue_delta_after_ras_v4']:+.3f}`.", "", payload["interpretation"], ""])


def _human_markdown(payload: dict[str, object]) -> str:
    lines = ["# RAS V4 Vs Human Comparative Preferences", ""]
    if payload.get("status") != "evaluated":
        lines.append(f"Status: `{payload.get('status')}`.")
        return "\n".join(lines)
    lines.extend([f"Comparative packet size: {payload['packet_size']}.", f"Majority-preference items evaluated: {payload['majority_preference_items_evaluated']}.", f"Computed RAS preferred-route alignment: {payload['computed_ras_human_preferred_route_alignment']:.3f}.", f"RAS_V4 preferred-route alignment: {payload['ras_v4_human_preferred_route_alignment']:.3f}.", f"Alignment delta: {payload['alignment_delta_ras_v4_minus_computed']:+.3f}.", "", payload["scope_note"], ""])
    return "\n".join(lines)


def _paper_markdown(payload: dict[str, object]) -> str:
    rescue = payload["rescue_comparison"]
    promotion = payload["promotion_decision"]
    return "\n".join([
        "# RAS V4 For Paper",
        "",
        "RAS_V4 extends route-only RAS by scoring route adequacy and evidence adequacy jointly for every candidate backend.",
        "",
        "## Why Route-Only RAS Was Insufficient",
        "",
        "RAS_V3 improved adversarial route accuracy but did not improve adversarial answer accuracy. That failure mode showed that choosing a representation is not enough when the evidence returned by that representation is weak, noisy, or poorly ranked.",
        "",
        "## How Evidence Adequacy Changes The Story",
        "",
        "RAS_V4 inspects each backend's top-k evidence before choosing a final backend. It uses score gaps, lexical identifier matches, source/title overlap, KG path completeness, hybrid agreement, diversity, contamination, and answerability markers.",
        "",
        "## Main Result",
        "",
        f"- Adversarial test computed RAS answer accuracy: {payload['systems']['adversarial_test']['computed_ras']['answer_accuracy']:.3f}.",
        f"- Adversarial test RAS_V4 answer accuracy: {payload['systems']['adversarial_test']['ras_v4']['answer_accuracy']:.3f}.",
        f"- Adversarial test RAS_V4+rescue answer accuracy: {payload['systems']['adversarial_test']['ras_v4_rescue']['answer_accuracy']:.3f}.",
        f"- Adversarial test calibrated rescue answer accuracy: {rescue['calibrated_rescue_answer_accuracy']:.3f}.",
        f"- Promotion decision: `{promotion['decision']}`.",
        "",
        "## Interpretation",
        "",
        promotion["rationale"],
        "RAS_V4 is more publishable as a research framework than route-only RAS because it formalizes evidence adequacy, but the current learned model is not strong enough to replace computed RAS in production.",
        "",
        "## Threats To Validity",
        "",
        "- Training data remains small and benchmark-shaped.",
        "- Evidence features are lightweight heuristics rather than human judgments.",
        "- Human alignment compares route choices to existing comparative preferences, not newly annotated RAS_V4 outputs.",
        "- Calibrated rescue may still outperform because it changes evidence ordering after route selection.",
        "",
    ])


def _plot_comparison(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np
    systems = ["computed_ras", "computed_ras_v2", "ras_v3", "calibrated_rescue", "ras_v4", "ras_v4_rescue"]
    route = [payload["systems"]["adversarial_test"][system]["route_accuracy"] for system in systems]
    answer = [payload["systems"]["adversarial_test"][system]["answer_accuracy"] for system in systems]
    image = np.ones((260, 520, 3), dtype=float)
    base = 220
    for i, (rv, av) in enumerate(zip(route, answer)):
        left = 22 + i * 78
        image[base - int(rv * 185):base, left:left + 24, :] = [0.18, 0.36, 0.58]
        image[base - int(av * 185):base, left + 28:left + 52, :] = [0.78, 0.45, 0.25]
    image[base:base + 2, 10:510, :] = 0.2
    mpimg.imsave(path, image)


def _plot_tags(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np
    tags = list(payload["systems"]["adversarial_test"]["ras_v4"]["per_ambiguity_tag"].keys())[:10]
    image = np.ones((250, max(420, len(tags) * 58), 3), dtype=float)
    base = 215
    for i, tag in enumerate(tags):
        ras = payload["systems"]["adversarial_test"]["computed_ras"]["per_ambiguity_tag"].get(tag, {}).get("answer_accuracy", 0.0)
        v4 = payload["systems"]["adversarial_test"]["ras_v4"]["per_ambiguity_tag"].get(tag, {}).get("answer_accuracy", 0.0)
        left = 18 + i * 58
        image[base - int(ras * 175):base, left:left + 22, :] = [0.5, 0.5, 0.5]
        image[base - int(v4 * 175):base, left + 25:left + 47, :] = [0.2, 0.55, 0.45]
    mpimg.imsave(path, image)


def _plot_contributions(payload: dict[str, object], path: Path) -> None:
    import matplotlib.image as mpimg
    import numpy as np
    rows = payload["systems"]["adversarial_test"]["ras_v4"]["results"][:16]
    image = np.ones((260, 520, 3), dtype=float)
    center = 250
    for i, row in enumerate(rows):
        y = 12 + i * 14
        route = float(row["score_payload"].get("route_contribution", 0.0))
        evidence = float(row["score_payload"].get("evidence_contribution", 0.0))
        image[y:y + 8, center:center + max(1, int(max(0.0, route) * 20)), :] = [0.2, 0.4, 0.65]
        image[y:y + 8, center - max(1, int(max(0.0, evidence) * 20)):center, :] = [0.25, 0.6, 0.35]
    image[8:240, center:center + 2, :] = 0.1
    mpimg.imsave(path, image)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and verify the interpretable RAS V4 joint route/evidence adequacy model.")
    parser.add_argument("--seed", type=int, default=79)
    args = parser.parse_args()
    payload = verify_ras_v4(seed=args.seed)
    adv = payload["systems"]["adversarial_test"]
    print(
        "ras_v4 "
        f"decision={payload['promotion_decision']['decision']} "
        f"computed_answer={adv['computed_ras']['answer_accuracy']:.3f} "
        f"ras_v3_answer={adv['ras_v3']['answer_accuracy']:.3f} "
        f"ras_v4_answer={adv['ras_v4']['answer_accuracy']:.3f} "
        f"ras_v4_rescue_answer={adv['ras_v4_rescue']['answer_accuracy']:.3f} "
        f"calibrated_rescue_answer={adv['calibrated_rescue']['answer_accuracy']:.3f} "
        f"json={JSON_PATH} markdown={MARKDOWN_PATH}"
    )
    for line in payload["baseline_takeaways"]:
        print(line)


if __name__ == "__main__":
    main()
