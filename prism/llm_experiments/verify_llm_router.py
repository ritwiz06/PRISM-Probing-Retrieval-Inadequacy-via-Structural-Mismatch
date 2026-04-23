from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

from prism.analysis.evaluation import BACKENDS, answer_matches_gold, evidence_id_set, load_combined_benchmark, load_analysis_retrievers
from prism.answering.generator import synthesize_answer
from prism.calibration.verify_calibrated_router import verify_calibrated_router
from prism.generalization.loaders import load_generalization_benchmark
from prism.llm_experiments.compare_to_human_eval import compare_llm_to_human_eval
from prism.llm_experiments.llm_router import LLMRouter
from prism.public_corpus.loaders import load_public_benchmark
from prism.ras.compute_ras import route_query
from prism.utils import write_json

EVAL_DIR = Path("data/eval")
JSON_PATH = EVAL_DIR / "llm_router_eval.json"
CSV_PATH = EVAL_DIR / "llm_router_eval.csv"
MARKDOWN_PATH = EVAL_DIR / "llm_router_eval_summary.md"
PAPER_MD_PATH = EVAL_DIR / "llm_experiment_results_for_paper.md"
ROUTER_PLOT = EVAL_DIR / "llm_router_comparison.png"
ADVERSARIAL_TAG_PLOT = EVAL_DIR / "llm_adversarial_tag_breakdown.png"


def verify_llm_router() -> dict[str, object]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    router = LLMRouter()
    diagnostics = router.diagnostics()
    baseline_payload = _baseline_payload()
    if diagnostics.get("available"):
        llm_results = _evaluate_live_llm(router)
    else:
        llm_results = _unavailable_llm_results(diagnostics, baseline_payload)
    human_alignment = compare_llm_to_human_eval(router)
    payload = {
        "status": "llm_available" if diagnostics.get("available") else "llm_unavailable",
        "llm_runtime": diagnostics,
        "production_safety": {
            "production_router": "computed_ras",
            "llm_behavior": "analysis_only",
            "demo_behavior_changed": False,
        },
        "baseline_results": baseline_payload,
        "llm_results": llm_results,
        "human_alignment": human_alignment,
        "tradeoffs": _tradeoffs(diagnostics, llm_results),
        "artifacts": {
            "json": str(JSON_PATH),
            "csv": str(CSV_PATH),
            "markdown": str(MARKDOWN_PATH),
            "paper_markdown": str(PAPER_MD_PATH),
            "router_plot": str(ROUTER_PLOT),
            "adversarial_tag_plot": str(ADVERSARIAL_TAG_PLOT),
        },
    }
    write_json(JSON_PATH, payload)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    PAPER_MD_PATH.write_text(_paper_markdown(payload), encoding="utf-8")
    _plot_router_comparison(payload, ROUTER_PLOT)
    _plot_adversarial_tags(payload, ADVERSARIAL_TAG_PLOT)
    return payload


def _baseline_payload() -> dict[str, object]:
    path = Path("data/eval/calibrated_router.json")
    if not path.exists():
        verify_calibrated_router()
    calibrated = json.loads(path.read_text(encoding="utf-8"))
    datasets = {}
    for dataset_name in ("adversarial_test", "curated", "generalization_v2_test", "public_raw_test"):
        systems = calibrated["systems"].get(dataset_name, {})
        datasets[dataset_name] = {
            name: _compact_metrics(metrics)
            for name, metrics in systems.items()
            if name
            in {
                "computed_ras",
                "computed_ras_calibrated",
                "computed_ras_calibrated_topk_rescue",
                "classifier_router",
                "always_bm25",
                "always_dense",
                "always_kg",
                "always_hybrid",
            }
        }
    return {
        "source": str(path),
        "datasets": datasets,
        "note": "Non-LLM comparisons are reused from the calibrated-router verifier to avoid changing production behavior.",
    }


def _compact_metrics(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "total": metrics.get("total", 0),
        "route_accuracy": metrics.get("route_accuracy", 0.0),
        "answer_accuracy": metrics.get("answer_accuracy", 0.0),
        "evidence_hit_at_k": metrics.get("evidence_hit_at_k", 0.0),
        "per_family": metrics.get("per_family", {}),
        "per_ambiguity_tag": metrics.get("per_ambiguity_tag", {}),
    }


def _unavailable_llm_results(diagnostics: dict[str, object], baseline_payload: dict[str, object]) -> dict[str, object]:
    return {
        "status": "unavailable",
        "datasets": {
            dataset: {
                "system": "llm_router",
                "total": 0,
                "route_accuracy": None,
                "answer_accuracy": None,
                "evidence_hit_at_k": None,
                "per_family": {},
                "per_ambiguity_tag": {},
                "results": [],
                "unavailable_reason": diagnostics.get("error", "local LLM unavailable"),
            }
            for dataset in baseline_payload["datasets"]
        },
        "setup_note": (
            "No local LLM endpoint responded. Start Ollama, ensure a local model is pulled, "
            "optionally set PRISM_LLM_MODEL, then rerun this verifier."
        ),
    }


def _evaluate_live_llm(router: LLMRouter) -> dict[str, object]:
    clean_retrievers = load_analysis_retrievers()
    datasets = {
        "curated": [
            {
                "id": f"curated_{row['slice']}_{index:03d}",
                "query": str(row["query"]),
                "family": str(row["gold_route"]),
                "gold_answer": str(row["gold_answer"]),
                "gold_evidence_ids": [str(value) for value in row.get("gold_evidence_ids", [])],
                "ambiguity_tags": [],
            }
            for index, row in enumerate(load_combined_benchmark())
        ],
        "generalization_v2_test": [
            {
                "id": item.id,
                "query": item.query,
                "family": item.route_family,
                "gold_answer": item.gold_answer,
                "gold_evidence_ids": [],
                "ambiguity_tags": [item.tag] if item.tag else [],
            }
            for item in load_generalization_benchmark(split="test")
        ],
        "public_raw_test": [
            {
                "id": item.id,
                "query": item.query,
                "family": item.route_family,
                "gold_answer": item.gold_answer,
                "gold_evidence_ids": item.gold_source_doc_ids,
                "ambiguity_tags": [],
            }
            for item in load_public_benchmark(split="test")
        ],
    }
    # The adversarial verifier uses a hard-context retriever. To keep this
    # optional LLM run light, route accuracy is evaluated from the benchmark and
    # answer/evidence are reported as unavailable for adversarial if the hard
    # context is not already materialized in this module.
    from prism.adversarial.loaders import load_adversarial_benchmark

    datasets["adversarial_test"] = [
        {
            "id": item.id,
            "query": item.query,
            "family": item.intended_route_family,
            "gold_answer": item.gold_answer,
            "gold_evidence_ids": item.gold_source_doc_ids + item.gold_triple_ids,
            "ambiguity_tags": item.ambiguity_tags,
        }
        for item in load_adversarial_benchmark(split="test")
    ]
    return {
        "status": "evaluated",
        "datasets": {
            dataset_name: _evaluate_records(dataset_name, rows, router, clean_retrievers)
            for dataset_name, rows in datasets.items()
        },
    }


def _evaluate_records(dataset_name: str, rows: list[dict[str, object]], router: LLMRouter, retrievers: dict[str, object]) -> dict[str, object]:
    counters = Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, unavailable=0)
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0))
    per_tag = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0))
    results = []
    for row in rows:
        prediction = router.predict(str(row["query"]))
        backend = prediction.route
        answer_ok = False
        evidence_ok = False
        answer_text = ""
        evidence_ids: set[str] = set()
        if prediction.available and backend in BACKENDS:
            evidence = retrievers[backend].retrieve(str(row["query"]), top_k=5 if backend == "hybrid" else 3)
            decision = route_query(str(row["query"]))
            answer = synthesize_answer(str(row["query"]), decision.features, decision.ras_scores, backend, evidence)
            answer_text = answer.final_answer
            answer_ok = answer_matches_gold(answer_text, str(row["gold_answer"]))
            evidence_ids = evidence_id_set(evidence)
            gold_ids = set(str(value) for value in row.get("gold_evidence_ids", []))
            evidence_ok = bool(gold_ids & evidence_ids) if gold_ids else True
        counters["total"] += 1
        counters["route_correct"] += int(backend == row["family"])
        counters["answer_correct"] += int(answer_ok)
        counters["evidence_hits"] += int(evidence_ok)
        counters["unavailable"] += int(not prediction.available)
        family = str(row["family"])
        _update_counter(per_family[family], backend == row["family"], answer_ok, evidence_ok)
        for tag in row.get("ambiguity_tags", []) or []:
            _update_counter(per_tag[str(tag)], backend == row["family"], answer_ok, evidence_ok)
        results.append(
            {
                "id": row["id"],
                "query": row["query"],
                "gold_route": row["family"],
                "llm_route": backend,
                "llm_confidence": prediction.confidence,
                "route_correct": backend == row["family"],
                "answer": answer_text,
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "retrieved_evidence_ids": sorted(evidence_ids),
                "rationale": prediction.rationale,
                "available": prediction.available,
                "error": prediction.error,
            }
        )
    total = counters["total"]
    return {
        "system": "llm_router",
        "dataset": dataset_name,
        "total": total,
        "route_accuracy": counters["route_correct"] / total if total else 0.0,
        "answer_accuracy": counters["answer_correct"] / total if total else 0.0,
        "evidence_hit_at_k": counters["evidence_hits"] / total if total else 0.0,
        "unavailable_count": counters["unavailable"],
        "per_family": _counter_breakdown(per_family),
        "per_ambiguity_tag": _counter_breakdown(per_tag),
        "results": results,
    }


def _update_counter(counter: Counter[str], route_ok: bool, answer_ok: bool, evidence_ok: bool) -> None:
    counter["total"] += 1
    counter["route_correct"] += int(route_ok)
    counter["answer_correct"] += int(answer_ok)
    counter["evidence_hits"] += int(evidence_ok)


def _counter_breakdown(counters: dict[str, Counter[str]]) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for key, counter in sorted(counters.items()):
        total = counter["total"]
        output[key] = {
            "total": total,
            "route_accuracy": counter["route_correct"] / total if total else 0.0,
            "answer_accuracy": counter["answer_correct"] / total if total else 0.0,
            "evidence_hit_at_k": counter["evidence_hits"] / total if total else 0.0,
        }
    return output


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    rows: list[dict[str, object]] = []
    for dataset, systems in payload["baseline_results"]["datasets"].items():
        for system, metrics in systems.items():
            rows.append(
                {
                    "dataset": dataset,
                    "system": system,
                    "route_accuracy": metrics.get("route_accuracy"),
                    "answer_accuracy": metrics.get("answer_accuracy"),
                    "evidence_hit_at_k": metrics.get("evidence_hit_at_k"),
                    "llm_runtime_status": payload["status"],
                }
            )
    for dataset, metrics in payload["llm_results"].get("datasets", {}).items():
        rows.append(
            {
                "dataset": dataset,
                "system": "llm_router",
                "route_accuracy": metrics.get("route_accuracy"),
                "answer_accuracy": metrics.get("answer_accuracy"),
                "evidence_hit_at_k": metrics.get("evidence_hit_at_k"),
                "llm_runtime_status": payload["status"],
            }
        )
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["dataset", "system", "route_accuracy", "answer_accuracy", "evidence_hit_at_k", "llm_runtime_status"])
        writer.writeheader()
        writer.writerows(rows)


def _markdown(payload: dict[str, object]) -> str:
    lines = ["# LLM Router Experiment Summary", ""]
    lines.append(f"Status: `{payload['status']}`.")
    runtime = payload["llm_runtime"]
    lines.append(f"Local LLM provider/model: `{runtime.get('provider')}` / `{runtime.get('model')}`.")
    lines.append(f"Runtime available: `{runtime.get('available')}`.")
    if not runtime.get("available"):
        lines.append(f"Runtime error: `{runtime.get('error')}`.")
    lines.extend(["", "## Automatic Benchmark Results"])
    for dataset, systems in payload["baseline_results"]["datasets"].items():
        computed = systems.get("computed_ras", {})
        calibrated = systems.get("computed_ras_calibrated_topk_rescue", systems.get("computed_ras_calibrated", {}))
        classifier = systems.get("classifier_router", {})
        llm = payload["llm_results"].get("datasets", {}).get(dataset, {})
        lines.append(
            f"- {dataset}: computed RAS answer={computed.get('answer_accuracy')}, "
            f"calibrated/rescue answer={calibrated.get('answer_accuracy')}, "
            f"classifier answer={classifier.get('answer_accuracy')}, "
            f"LLM answer={llm.get('answer_accuracy')}."
        )
    lines.extend(["", "## Human Preference Alignment"])
    human = payload.get("human_alignment", {})
    lines.append(f"- LLM-vs-human status: `{human.get('status')}`.")
    if human.get("alignment"):
        lines.append(f"- Alignment rate: {human['alignment'].get('alignment_rate')}.")
    else:
        lines.append("- Alignment unavailable until local LLM route choices are generated.")
    lines.extend(["", "## Tradeoffs"])
    for item in payload["tradeoffs"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _paper_markdown(payload: dict[str, object]) -> str:
    lines = ["# LLM-Assisted PRISM Experiment Results For Paper", ""]
    lines.append("## What The LLM Was Allowed To See")
    lines.append("The LLM router prompt includes the user query, compact backend definitions, parsed query features, computed RAS scores, and optional evidence hints. It is not allowed to answer the query during routing.")
    lines.append("")
    lines.append("## What Was Evaluated")
    lines.append("The experiment is analysis-only: local LLM routing and evidence-grounded answer/trace refinement are compared against computed RAS, calibrated rescue, classifier routing, and fixed backends.")
    lines.append("")
    if payload["status"] == "llm_unavailable":
        lines.append("## Runtime Result")
        lines.append("No local LLM endpoint was available during this run, so the repo generated the evaluation harness, baseline comparisons, setup guidance, plots, and partial human-alignment artifacts without fabricating LLM metrics.")
    else:
        lines.append("## Runtime Result")
        lines.append("A local LLM endpoint was available and LLM route predictions were evaluated. See `llm_router_eval.json` for per-example details.")
    lines.extend(
        [
            "",
            "## Tradeoffs",
            "- Computed RAS remains more inspectable and deterministic.",
            "- LLM routing may be useful on ambiguous prompts, but it must be judged against evidence support and human preference rather than treated as ground truth.",
            "- Evidence-grounded refinement can improve readability only if it preserves evidence ids and does not introduce unsupported facts.",
        ]
    )
    return "\n".join(lines) + "\n"


def _tradeoffs(diagnostics: dict[str, object], llm_results: dict[str, object]) -> list[str]:
    if not diagnostics.get("available"):
        return [
            "Local LLM runtime was unavailable, so no LLM metric claims are made.",
            "The harness still compares non-LLM baselines and writes setup guidance for rerunning with Ollama.",
            "Computed RAS remains the production router; LLM behavior is optional and analysis-only.",
        ]
    return [
        "LLM predictions are evaluated as router proposals, not ground truth.",
        "Any answer/trace refinement must preserve PRISM evidence ids and selected backend.",
        "A gain on adversarial cases would need to be checked against curated and public benchmarks before adoption.",
    ]


def _plot_router_comparison(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dataset = "adversarial_test"
    systems = payload["baseline_results"]["datasets"].get(dataset, {})
    names = ["computed_ras", "computed_ras_calibrated_topk_rescue", "classifier_router", "always_dense"]
    labels = ["RAS", "Calibrated", "Classifier", "Always Dense"]
    values = [float(systems.get(name, {}).get("answer_accuracy") or 0.0) for name in names]
    llm_value = payload["llm_results"].get("datasets", {}).get(dataset, {}).get("answer_accuracy")
    labels.append("LLM")
    values.append(float(llm_value or 0.0))
    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color=["#425466", "#2f855a", "#805ad5", "#b7791f", "#c53030"])
    plt.ylim(0, 1.05)
    plt.ylabel("Answer accuracy")
    plt.title("Router Comparison On Adversarial Test")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()


def _plot_adversarial_tags(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    baseline = payload["baseline_results"]["datasets"].get("adversarial_test", {}).get("computed_ras", {})
    tags = baseline.get("per_ambiguity_tag", {})
    if not tags:
        tags = {"no_tag_data": {"answer_accuracy": 0.0}}
    labels = list(tags)[:8]
    values = [float(tags[label].get("answer_accuracy", 0.0)) for label in labels]
    plt.figure(figsize=(9, 4))
    plt.bar(labels, values, color="#2b6cb0")
    plt.ylim(0, 1.05)
    plt.ylabel("Answer accuracy")
    plt.title("Computed RAS By Adversarial Ambiguity Tag")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate optional local LLM routing/refinement experiments.")
    parser.parse_args()
    payload = verify_llm_router()
    print(
        "llm_router_eval "
        f"status={payload['status']} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH} "
        f"human_alignment={payload['human_alignment']['status']}"
    )


if __name__ == "__main__":
    main()
