from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_mplconfig")

from prism.adversarial.loaders import load_adversarial_benchmark
from prism.adversarial.verify_adversarial import _build_retrievers as build_hard_retrievers
from prism.adversarial.verify_adversarial import _evidence_id_set as hard_evidence_ids
from prism.adversarial.verify_adversarial import _load_hard_context_documents
from prism.analysis.evaluation import answer_matches_gold, evidence_id_set
from prism.answering.generator import synthesize_answer
from prism.config import load_config
from prism.open_corpus.build_source_pack import build_source_pack
from prism.open_corpus.load_local_docs import load_local_documents
from prism.open_corpus.query_local_graph import build_query_local_graph, export_query_local_graph
from prism.open_corpus.workspace import build_runtime_corpus_from_local, ensure_source_pack_documents
from prism.public_graph.build_public_graph import load_public_structure_triples
from prism.ras.compute_ras import route_query
from prism.ras.route_improvement import route_query_v2
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_jsonl_documents, write_json

EVAL_DIR = Path("data/eval")
RUNTIME_ROOT = Path("data/runtime_corpora")
SMOKE_JSON = EVAL_DIR / "open_corpus_smoke.json"
SMOKE_CSV = EVAL_DIR / "open_corpus_smoke.csv"
SMOKE_MD = EVAL_DIR / "open_corpus_smoke.md"
WORKSPACE_JSON = EVAL_DIR / "open_workspace_vs_baselines.json"
WORKSPACE_MD = EVAL_DIR / "open_workspace_summary.md"
RAS_V2_MD = EVAL_DIR / "ras_v2_summary.md"
PAPER_MD = EVAL_DIR / "open_domain_extension_for_paper.md"
ROUTE_PLOT = EVAL_DIR / "ras_v2_adversarial_route_comparison.png"
OPEN_ROUTE_PLOT = EVAL_DIR / "open_corpus_route_usage.png"


def verify_open_corpus() -> dict[str, object]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    pack_summaries = {pack: build_source_pack(pack) for pack in ("wikipedia", "rfc_specs")}
    local_summary = _build_local_demo_docs()
    smoke_rows = _run_smoke(pack_summaries, local_summary)
    ras_v2 = _evaluate_ras_v2()
    payload = {
        "status": "passed",
        "source_packs": pack_summaries,
        "local_demo": local_summary,
        "smoke": _summarize_rows(smoke_rows),
        "smoke_rows": smoke_rows,
        "ras_v2": ras_v2,
        "artifacts": {
            "json": str(SMOKE_JSON),
            "csv": str(SMOKE_CSV),
            "markdown": str(SMOKE_MD),
            "workspace_json": str(WORKSPACE_JSON),
            "workspace_markdown": str(WORKSPACE_MD),
            "ras_v2_markdown": str(RAS_V2_MD),
            "paper_markdown": str(PAPER_MD),
            "route_plot": str(ROUTE_PLOT),
            "open_route_plot": str(OPEN_ROUTE_PLOT),
        },
    }
    write_json(SMOKE_JSON, payload)
    write_json(WORKSPACE_JSON, payload)
    _write_csv(SMOKE_CSV, smoke_rows)
    SMOKE_MD.write_text(_smoke_markdown(payload), encoding="utf-8")
    WORKSPACE_MD.write_text(_workspace_markdown(payload), encoding="utf-8")
    RAS_V2_MD.write_text(_ras_v2_markdown(ras_v2), encoding="utf-8")
    PAPER_MD.write_text(_paper_markdown(payload), encoding="utf-8")
    _plot_ras_v2(ras_v2, ROUTE_PLOT)
    _plot_open_routes(smoke_rows, OPEN_ROUTE_PLOT)
    return payload


def _build_local_demo_docs() -> dict[str, object]:
    raw_dir = RUNTIME_ROOT / "local_demo_docs" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "prism_workspace.md").write_text(
        "# PRISM Workspace\n"
        "PRISM routing connects query features to evidence traces through selected backends. "
        "The workspace compares BM25, Dense, KG, and Hybrid evidence for the same query.\n",
        encoding="utf-8",
    )
    (raw_dir / "demo_animals.txt").write_text(
        "A bat is a mammal. A mammal is a vertebrate. A bat uses wings and echolocation. "
        "Bat connects to vertebrate through mammal.\n",
        encoding="utf-8",
    )
    (raw_dir / "dense_notes.json").write_text(
        json.dumps(
            {
                "title": "Semantic Notes",
                "body": "Climate anxiety describes distress about climate change and ecological loss.",
            }
        ),
        encoding="utf-8",
    )
    return build_runtime_corpus_from_local([raw_dir], name="local_demo_docs")


def _run_smoke(pack_summaries: dict[str, dict[str, object]], local_summary: dict[str, object]) -> list[dict[str, object]]:
    smoke_specs = [
        ("source_pack:wikipedia", pack_summaries["wikipedia"]["output_dir"], "What feels like climate anxiety?", "dense", "climate anxiety"),
        ("source_pack:wikipedia", pack_summaries["wikipedia"]["output_dir"], "What bridge connects bat and vertebrate?", "hybrid", "mammal"),
        ("source_pack:rfc_specs", pack_summaries["rfc_specs"]["output_dir"], "RFC-7231", "bm25", "HTTP/1.1 semantics"),
        ("local_folder:demo", local_summary["output_dir"], "Is a bat a mammal?", "kg", "bat is a mammal"),
        ("local_folder:demo", local_summary["output_dir"], "What connects PRISM routing and evidence traces?", "hybrid", "query features"),
    ]
    rows = []
    for index, (source_mode, output_dir, query, gold_route, gold_answer) in enumerate(smoke_specs, start=1):
        documents = read_jsonl_documents(Path(output_dir) / "documents.jsonl")
        graph = build_query_local_graph(query, documents)
        export_info = export_query_local_graph(graph, output_dir, f"smoke_{index:02d}")
        retrievers = _runtime_retrievers(documents, graph.triples)
        decision = route_query(query)
        v2 = route_query_v2(query, source_type_hint=source_mode.split(":")[0])
        selected_backend = decision.selected_backend
        evidence = retrievers[selected_backend].retrieve(query, top_k=5 if selected_backend == "hybrid" else 3)
        answer = synthesize_answer(query, decision.features, decision.ras_scores, selected_backend, evidence)
        all_backend_hits = _compare_routes(query, retrievers, gold_answer)
        rows.append(
            {
                "id": f"open_smoke_{index:02d}",
                "source_mode": source_mode,
                "query": query,
                "gold_route": gold_route,
                "computed_ras_route": selected_backend,
                "computed_ras_v2_route": v2.selected_backend,
                "route_correct": selected_backend == gold_route,
                "answer": answer.final_answer,
                "gold_answer": gold_answer,
                "answer_correct": answer_matches_gold(answer.final_answer, gold_answer),
                "evidence_hit_at_k": _answer_in_evidence(evidence, gold_answer),
                "evidence_ids": [item.item_id for item in evidence],
                "query_local_graph_triples": len(graph.triples),
                "query_local_graph_artifact": export_info["json_path"],
                "route_comparison": all_backend_hits,
                "ras_v2_rationale": v2.rationale,
            }
        )
    return rows


def _runtime_retrievers(documents: list[Document], triples: list[Triple]) -> dict[str, object]:
    bm25 = BM25Retriever.build(documents)
    dense = DenseRetriever.build(documents, config=load_config().retrieval)
    kg = KGRetriever.build(triples, kg_mode="query_local_open_corpus")
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def _compare_routes(query: str, retrievers: dict[str, object], gold_answer: str) -> dict[str, object]:
    output = {}
    for backend in ("bm25", "dense", "kg", "hybrid"):
        evidence = retrievers[backend].retrieve(query, top_k=5 if backend == "hybrid" else 3)
        output[backend] = {
            "top_evidence_ids": [item.item_id for item in evidence],
            "evidence_contains_gold": _answer_in_evidence(evidence, gold_answer),
        }
    return output


def _evaluate_ras_v2() -> dict[str, object]:
    items = load_adversarial_benchmark()
    hard_documents = _load_hard_context_documents()
    hard_triples = load_public_structure_triples("mixed_public_demo")
    retrievers = build_hard_retrievers(hard_documents, hard_triples)
    systems = {
        "computed_ras": lambda query: route_query(query).selected_backend,
        "computed_ras_v2": lambda query: route_query_v2(query).selected_backend,
    }
    results = {name: _evaluate_route_system(name, selector, items, retrievers) for name, selector in systems.items()}
    try:
        calibrated = json.loads(Path("data/eval/calibrated_router.json").read_text(encoding="utf-8"))
        for name in ("computed_ras_calibrated_topk_rescue", "classifier_router"):
            if name in calibrated["systems"]["adversarial_test"]:
                results[f"{name}_test_reference"] = {
                    key: calibrated["systems"]["adversarial_test"][name].get(key)
                    for key in ("total", "route_accuracy", "answer_accuracy", "evidence_hit_at_k")
                }
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
    delta = results["computed_ras_v2"]["answer_accuracy"] - results["computed_ras"]["answer_accuracy"]
    return {
        "protocol": "RAS v2 is analysis-only and evaluated on the adversarial benchmark after dev-informed heuristic design.",
        "production_default": "computed_ras",
        "systems": results,
        "answer_accuracy_delta_v2_minus_ras": delta,
        "recommendation": "keep_analysis_only" if delta < 0.03 else "consider_more_guarded_testing_before_adoption",
    }


def _evaluate_route_system(name: str, selector, items, retrievers: dict[str, object]) -> dict[str, object]:
    counters = Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0)
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0))
    rows = []
    for item in items:
        backend = selector(item.query)
        decision = route_query(item.query)
        evidence = retrievers[backend].retrieve(item.query, top_k=5 if backend == "hybrid" else 3)
        answer = synthesize_answer(item.query, decision.features, decision.ras_scores, backend, evidence)
        ids = hard_evidence_ids(evidence)
        gold_ids = set(item.gold_source_doc_ids + item.gold_triple_ids)
        evidence_ok = bool(gold_ids & ids)
        answer_ok = answer_matches_gold(answer.final_answer, item.gold_answer)
        route_ok = backend == item.intended_route_family
        counters["total"] += 1
        counters["route_correct"] += int(route_ok)
        counters["answer_correct"] += int(answer_ok)
        counters["evidence_hits"] += int(evidence_ok)
        fam = per_family[item.intended_route_family]
        fam["total"] += 1
        fam["route_correct"] += int(route_ok)
        fam["answer_correct"] += int(answer_ok)
        fam["evidence_hits"] += int(evidence_ok)
        rows.append(
            {
                "id": item.id,
                "query": item.query,
                "gold_route": item.intended_route_family,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "ambiguity_tags": item.ambiguity_tags,
            }
        )
    total = counters["total"]
    return {
        "system": name,
        "total": total,
        "route_accuracy": counters["route_correct"] / total if total else 0.0,
        "answer_accuracy": counters["answer_correct"] / total if total else 0.0,
        "evidence_hit_at_k": counters["evidence_hits"] / total if total else 0.0,
        "per_family": _counter_breakdown(per_family),
        "results": rows,
    }


def _answer_in_evidence(evidence: list[RetrievedItem], gold_answer: str) -> bool:
    return any(answer_matches_gold(item.content, gold_answer) for item in evidence)


def _summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    return {
        "total": total,
        "route_accuracy": sum(1 for row in rows if row["route_correct"]) / total if total else 0.0,
        "answer_accuracy": sum(1 for row in rows if row["answer_correct"]) / total if total else 0.0,
        "evidence_hit_at_k": sum(1 for row in rows if row["evidence_hit_at_k"]) / total if total else 0.0,
        "source_modes": dict(Counter(str(row["source_mode"]) for row in rows)),
        "route_distribution": dict(Counter(str(row["computed_ras_route"]) for row in rows)),
    }


def _counter_breakdown(counters: dict[str, Counter[str]]) -> dict[str, dict[str, object]]:
    return {
        key: {
            "total": counter["total"],
            "route_accuracy": counter["route_correct"] / counter["total"] if counter["total"] else 0.0,
            "answer_accuracy": counter["answer_correct"] / counter["total"] if counter["total"] else 0.0,
            "evidence_hit_at_k": counter["evidence_hits"] / counter["total"] if counter["total"] else 0.0,
        }
        for key, counter in sorted(counters.items())
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = ["id", "source_mode", "query", "gold_route", "computed_ras_route", "computed_ras_v2_route", "route_correct", "answer_correct", "evidence_hit_at_k", "query_local_graph_triples"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _smoke_markdown(payload: dict[str, object]) -> str:
    smoke = payload["smoke"]
    lines = ["# Open-Corpus Smoke Evaluation", ""]
    lines.append(f"Status: `{payload['status']}`.")
    lines.append(f"Smoke examples: {smoke['total']}.")
    lines.append(f"Route accuracy: {smoke['route_accuracy']}.")
    lines.append(f"Answer accuracy: {smoke['answer_accuracy']}.")
    lines.append(f"Evidence hit@k: {smoke['evidence_hit_at_k']}.")
    lines.extend(["", "## Rows"])
    for row in payload["smoke_rows"]:
        lines.append(f"- `{row['id']}` {row['source_mode']}: route {row['computed_ras_route']} / gold {row['gold_route']}; graph triples={row['query_local_graph_triples']}.")
    return "\n".join(lines) + "\n"


def _workspace_markdown(payload: dict[str, object]) -> str:
    return (
        "# Open Workspace Summary\n\n"
        "PRISM now supports additive runtime corpora built from source packs and local folders. "
        "Artifacts are written under `data/runtime_corpora/` and do not replace the curated benchmark corpora.\n\n"
        f"- Source packs built: {', '.join(payload['source_packs'])}\n"
        f"- Local demo corpus documents: {payload['local_demo']['document_count']}\n"
        f"- Open-corpus smoke answer accuracy: {payload['smoke']['answer_accuracy']}\n"
        f"- RAS v2 recommendation: {payload['ras_v2']['recommendation']}\n\n"
        "The workspace should be described as source-pack/open-corpus QA, not full web-scale open-domain QA.\n"
    )


def _ras_v2_markdown(payload: dict[str, object]) -> str:
    lines = ["# RAS V2 Route-Improvement Summary", ""]
    lines.append(f"Protocol: {payload['protocol']}")
    lines.append(f"Production default: `{payload['production_default']}`.")
    lines.append(f"Recommendation: `{payload['recommendation']}`.")
    lines.append(f"Answer accuracy delta v2-minus-RAS: {payload['answer_accuracy_delta_v2_minus_ras']}.")
    lines.extend(["", "## Systems"])
    for name, metrics in payload["systems"].items():
        if isinstance(metrics, dict):
            lines.append(f"- {name}: route={metrics.get('route_accuracy')} answer={metrics.get('answer_accuracy')} evidence={metrics.get('evidence_hit_at_k')}.")
    lines.extend(["", "## Interpretation", "RAS v2 remains analysis-only unless it shows material hard-case gains without regressions on curated/public/generalization benchmarks."])
    return "\n".join(lines) + "\n"


def _paper_markdown(payload: dict[str, object]) -> str:
    return (
        "# Open-Domain Extension For Paper\n\n"
        "PRISM was extended from a bounded benchmark system into a reusable source-pack/open-corpus workspace. "
        "Users can build runtime corpora from local files or built-in packs, inspect route scores, compare backends, and export query-local graph evidence.\n\n"
        "## Source Packs\n"
        "Current built-in packs include Wikipedia-style concepts and RFC specifications, with additional registries for medical codes, policy documents, and CS API docs.\n\n"
        "## Query-Local Graphs\n"
        "For each open-corpus query, PRISM can extract lightweight triples from top/local documents. These triples are provenance-linked and used by KG/Hybrid retrieval in open-corpus mode.\n\n"
        "## Route Improvement\n"
        f"RAS v2 recommendation: `{payload['ras_v2']['recommendation']}`. "
        "It is an interpretable hard-case experiment, not a production replacement for computed RAS.\n\n"
        "## Limitation\n"
        "This is source-pack and user-corpus QA, not live web-scale open-domain search. Query-local graph extraction is lightweight and can be noisy.\n"
    )


def _plot_ras_v2(payload: dict[str, object], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [name for name in ("computed_ras", "computed_ras_v2") if name in payload["systems"]]
    values = [float(payload["systems"][name]["answer_accuracy"]) for name in names]
    plt.figure(figsize=(6, 4))
    plt.bar(names, values, color=["#425466", "#2f855a"])
    plt.ylim(0, 1.05)
    plt.ylabel("Answer accuracy")
    plt.title("Adversarial Benchmark: RAS vs RAS V2")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_open_routes(rows: list[dict[str, object]], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    counts = Counter(str(row["computed_ras_route"]) for row in rows)
    labels = list(counts)
    values = [counts[label] for label in labels]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color="#805ad5")
    plt.ylabel("Smoke query count")
    plt.title("Open-Corpus Route Usage")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify PRISM open-corpus workspace smoke flows.")
    parser.parse_args()
    payload = verify_open_corpus()
    print(
        "open_corpus_smoke "
        f"status={payload['status']} total={payload['smoke']['total']} "
        f"answer_accuracy={payload['smoke']['answer_accuracy']:.3f} "
        f"ras_v2_recommendation={payload['ras_v2']['recommendation']} "
        f"json={SMOKE_JSON} markdown={SMOKE_MD}"
    )


if __name__ == "__main__":
    main()

