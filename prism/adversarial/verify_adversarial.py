from __future__ import annotations

import argparse
import csv
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from prism.adversarial.benchmark_builder import build_adversarial_benchmark
from prism.adversarial.loaders import AdversarialItem, adversarial_counts, load_adversarial_benchmark
from prism.analysis.evaluation import BACKENDS, answer_matches_gold, load_combined_benchmark
from prism.app.pipeline import answer_query
from prism.generalization.noisy_corpus import NOISY_CORPUS_PATH, build_noisy_corpus
from prism.ingest.build_corpus import build_corpus
from prism.ingest.build_kg import build_kg
from prism.public_corpus.build_public_corpus import build_public_corpus
from prism.public_corpus.lexical_retriever import PublicAwareBM25Retriever, is_identifier_heavy_query
from prism.public_graph.build_public_graph import build_public_graph, load_public_structure_triples
from prism.ras.compute_ras import route_query
from prism.retrievers.bm25_retriever import BM25Retriever
from prism.retrievers.dense_retriever import DenseRetriever
from prism.retrievers.hybrid_retriever import HybridRetriever
from prism.retrievers.kg_retriever import KGRetriever
from prism.router_baselines.classifier_router import ClassifierRouter
from prism.router_baselines.route_confidence import compute_route_confidence
from prism.router_baselines.rule_router import RouterPrediction, keyword_rule_route
from prism.schemas import Document, RetrievedItem, Triple
from prism.utils import read_jsonl_documents, write_json

EVAL_DIR = Path("data/eval")
JSON_PATH = EVAL_DIR / "adversarial_eval.json"
CSV_PATH = EVAL_DIR / "adversarial_eval.csv"
MARKDOWN_PATH = EVAL_DIR / "adversarial_eval_summary.md"
CONFIDENCE_JSON_PATH = EVAL_DIR / "adversarial_confidence.json"
CONFIDENCE_MARKDOWN_PATH = EVAL_DIR / "adversarial_confidence_summary.md"
ABLATION_MARKDOWN_PATH = EVAL_DIR / "adversarial_ablation_summary.md"
BASELINE_PLOT = EVAL_DIR / "adversarial_baselines_by_tag.png"
CONFIDENCE_PLOT = EVAL_DIR / "adversarial_confidence_error_rate.png"
TOPK_PLOT = EVAL_DIR / "adversarial_top1_topk_gap.png"

ROUTER_SYSTEMS = ("computed_ras", "keyword_rule_router", "classifier_router", "random_router")
FIXED_SYSTEMS = ("always_bm25", "always_dense", "always_kg", "always_hybrid")
ALL_SYSTEMS = ROUTER_SYSTEMS + FIXED_SYSTEMS


def verify_adversarial(seed: int = 53) -> dict[str, object]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    benchmark_path = build_adversarial_benchmark()
    items = load_adversarial_benchmark(benchmark_path)
    documents = _load_hard_context_documents()
    triples = load_public_structure_triples("mixed_public_demo")
    retrievers = _build_retrievers(documents, triples)
    classifier = _train_classifier(seed)

    runs = {
        split: {
            system: _evaluate_system(system, [item for item in items if item.split == split], retrievers, classifier, seed)
            for system in ALL_SYSTEMS
        }
        for split in ("dev", "test")
    }
    combined_runs = {
        system: _evaluate_system(system, items, retrievers, classifier, seed)
        for system in ALL_SYSTEMS
    }
    confidence_payload = _confidence_analysis(items, combined_runs["computed_ras"], classifier)
    ablation_payload = _ablation_analysis(items, documents, triples, classifier, seed)
    payload = {
        "seed": seed,
        "benchmark": {
            "path": str(benchmark_path),
            "total": len(items),
            "counts": adversarial_counts(items),
            "note": "Hard ambiguity benchmark is separate from curated, external, generalization_v2, public raw, and public-structure suites.",
        },
        "retrieval_context": {
            "document_count": len(documents),
            "triple_count": len(triples),
            "corpus_mode": "noisy local corpus plus public raw corpus; mixed demo KG plus public graph triples",
        },
        "protocol": {
            "classifier_router": "Classifier is trained only on the curated 80-query benchmark and evaluated on the hard adversarial benchmark.",
            "production_router": "computed_ras remains the production router; all other routers and ablations are analysis-only.",
        },
        "systems": {"splits": runs, "combined": combined_runs},
        "strongest_fixed_backend": _strongest_fixed(combined_runs),
        "confidence": confidence_payload["summary"],
        "ablations": ablation_payload,
        "takeaways": _takeaways(runs, combined_runs, confidence_payload, ablation_payload),
        "threats_to_validity": _threats_to_validity(),
        "plots": {
            "baselines_by_tag": str(BASELINE_PLOT),
            "confidence_error_rate": str(CONFIDENCE_PLOT),
            "top1_topk_gap": str(TOPK_PLOT),
        },
    }
    write_json(JSON_PATH, payload)
    write_json(CONFIDENCE_JSON_PATH, confidence_payload)
    _write_csv(CSV_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    CONFIDENCE_MARKDOWN_PATH.write_text(_confidence_markdown(confidence_payload), encoding="utf-8")
    ABLATION_MARKDOWN_PATH.write_text(_ablation_markdown(ablation_payload), encoding="utf-8")
    _plot_baselines_by_tag(payload, BASELINE_PLOT)
    _plot_confidence(confidence_payload, CONFIDENCE_PLOT)
    _plot_top1_topk(payload, TOPK_PLOT)
    return payload


def _load_hard_context_documents() -> list[Document]:
    clean_path = build_corpus()
    noisy_summary = build_noisy_corpus(clean_path, NOISY_CORPUS_PATH)
    build_kg(corpus_path=str(clean_path))
    public_path = build_public_corpus()
    build_public_graph(public_path)
    return _dedupe_documents(read_jsonl_documents(noisy_summary["path"]) + read_jsonl_documents(public_path))


def _dedupe_documents(documents: list[Document]) -> list[Document]:
    by_id: dict[str, Document] = {}
    for document in documents:
        by_id[document.doc_id] = document
    return list(by_id.values())


def _build_retrievers(
    documents: list[Document],
    triples: list[Triple],
    *,
    public_lexical: bool = False,
    semantic_rerank: bool = True,
) -> dict[str, object]:
    bm25 = PublicAwareBM25Retriever.build(documents) if public_lexical else BM25Retriever.build(documents)
    dense = DenseRetriever(documents=documents, semantic_rerank=semantic_rerank)
    kg = KGRetriever.build(triples, kg_mode="adversarial_mixed_public_demo")
    hybrid = HybridRetriever([dense, kg, bm25])
    return {"bm25": bm25, "dense": dense, "kg": kg, "hybrid": hybrid}


def _train_classifier(seed: int) -> ClassifierRouter:
    rows = load_combined_benchmark()
    return ClassifierRouter(seed=seed).fit([str(row["query"]) for row in rows], [str(row["gold_route"]) for row in rows])


def _evaluate_system(
    system_name: str,
    items: list[AdversarialItem],
    retrievers: dict[str, object],
    classifier: ClassifierRouter,
    seed: int,
) -> dict[str, object]:
    rng = random.Random(seed)
    route_correct = 0
    answer_correct = 0
    evidence_hits = 0
    top1_hits = 0
    predicted_distribution: Counter[str] = Counter()
    confusion: Counter[str] = Counter()
    per_family = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    per_tag = defaultdict(lambda: Counter(total=0, route_correct=0, answer_correct=0, evidence_hits=0, top1_hits=0))
    rows: list[dict[str, object]] = []

    for item in items:
        prediction = _predict_route(system_name, item, rng, classifier, retrievers)
        backend = prediction.route
        payload = answer_query(
            item.query,
            top_k=5 if backend == "hybrid" else 3,
            retrievers=retrievers,
            backend_override=backend,
        )
        evidence = _payload_evidence(payload)
        evidence_ids = _evidence_id_set(evidence)
        top1_ok = _evidence_hit(item, evidence[:1], _evidence_id_set(evidence[:1]))
        evidence_ok = _evidence_hit(item, evidence, evidence_ids)
        final_answer = str(payload["answer"]["final_answer"])
        answer_ok = answer_matches_gold(final_answer, item.gold_answer)
        route_ok = backend == item.intended_route_family

        route_correct += int(route_ok)
        answer_correct += int(answer_ok)
        evidence_hits += int(evidence_ok)
        top1_hits += int(top1_ok)
        predicted_distribution[backend] += 1
        confusion[f"{item.intended_route_family}->{backend}"] += 1
        _update_counter(per_family[item.intended_route_family], route_ok, answer_ok, evidence_ok, top1_ok)
        for tag in item.ambiguity_tags:
            _update_counter(per_tag[tag], route_ok, answer_ok, evidence_ok, top1_ok)
        rows.append(
            {
                "id": item.id,
                "query": item.query,
                "split": item.split,
                "intended_route_family": item.intended_route_family,
                "ambiguity_tags": item.ambiguity_tags,
                "predicted_backend": backend,
                "route_correct": route_ok,
                "gold_answer": item.gold_answer,
                "answer": final_answer,
                "answer_correct": answer_ok,
                "evidence_hit": evidence_ok,
                "top1_evidence_hit": top1_ok,
                "top1_topk_gap": evidence_ok and not top1_ok,
                "gold_source_doc_ids": item.gold_source_doc_ids,
                "gold_triple_ids": item.gold_triple_ids,
                "top_evidence_ids": [entry.item_id for entry in evidence],
                "top_evidence_sources": [_evidence_source(entry) for entry in evidence],
                "router_scores": prediction.scores,
                "router_rationale": prediction.rationale,
            }
        )

    total = len(items)
    return {
        "system": system_name,
        "total": total,
        "route_accuracy": route_correct / total if total else 0.0,
        "answer_accuracy": answer_correct / total if total else 0.0,
        "evidence_hit_at_k": evidence_hits / total if total else 0.0,
        "top1_evidence_hit": top1_hits / total if total else 0.0,
        "top1_topk_gap_rate": (evidence_hits - top1_hits) / total if total else 0.0,
        "route_correct": route_correct,
        "answer_correct": answer_correct,
        "evidence_hits": evidence_hits,
        "top1_hits": top1_hits,
        "predicted_backend_distribution": dict(predicted_distribution),
        "confusion": dict(confusion),
        "per_family": _counter_breakdown(per_family),
        "per_ambiguity_tag": _counter_breakdown(per_tag),
        "results": rows,
    }


def _predict_route(
    system_name: str,
    item: AdversarialItem,
    rng: random.Random,
    classifier: ClassifierRouter,
    retrievers: dict[str, object],
) -> RouterPrediction:
    if system_name == "computed_ras":
        decision = route_query(item.query)
        return RouterPrediction(decision.selected_backend, decision.ras_scores, "Minimum computed RAS penalty.")
    if system_name == "keyword_rule_router":
        return keyword_rule_route(item.query)
    if system_name == "classifier_router":
        return classifier.predict(item.query)
    if system_name == "random_router":
        route = rng.choice(BACKENDS)
        return RouterPrediction(route, {backend: 0.25 for backend in BACKENDS}, "Fixed-seed random router.")
    if system_name == "computed_ras_public_arbitrated":
        decision = route_query(item.query)
        confidence = _lexical_confidence(item.query, retrievers)
        if is_identifier_heavy_query(item.query) and confidence.get("should_arbitrate"):
            return RouterPrediction("bm25", decision.ras_scores, f"Public lexical arbitration overrode {decision.selected_backend}; {confidence}.")
        return RouterPrediction(decision.selected_backend, decision.ras_scores, "Computed RAS with public lexical arbitration enabled.")
    if system_name.startswith("always_"):
        route = system_name.removeprefix("always_")
        return RouterPrediction(route, {backend: 1.0 if backend == route else 0.0 for backend in BACKENDS}, "Fixed-backend baseline.")
    raise ValueError(f"Unknown adversarial system: {system_name}")


def _lexical_confidence(query: str, retrievers: dict[str, object]) -> dict[str, object]:
    bm25 = retrievers.get("bm25")
    if hasattr(bm25, "lexical_confidence"):
        return bm25.lexical_confidence(query)  # type: ignore[no-any-return]
    return {"confidence": 0.0, "should_arbitrate": False, "matched_fields": [], "top_doc_id": "", "boost": 0.0}


def _payload_evidence(payload: dict[str, object]) -> list[RetrievedItem]:
    rows: list[RetrievedItem] = []
    for row in payload["top_evidence"]:
        rows.append(
            RetrievedItem(
                item_id=str(row["item_id"]),
                content=str(row["content"]),
                score=float(row["score"]),
                source_type=str(row["source_type"]),
                metadata=dict(row["metadata"]),
            )
        )
    return rows


def _evidence_id_set(evidence: list[RetrievedItem]) -> set[str]:
    ids: set[str] = set()
    for item in evidence:
        ids.add(item.item_id)
        for key in ("component_ids", "triple_id", "path_id", "parent_doc_id", "chunk_id", "source_doc_id", "kg_source_doc_id"):
            for part in str(item.metadata.get(key, "")).split(","):
                if part:
                    ids.add(part)
    return ids


def _evidence_source(item: RetrievedItem) -> str:
    for key in ("source_doc_id", "kg_source_doc_id", "parent_doc_id", "chunk_id"):
        value = item.metadata.get(key)
        if value:
            return str(value)
    return item.item_id


def _evidence_hit(item: AdversarialItem, evidence: list[RetrievedItem], evidence_ids: set[str]) -> bool:
    gold_ids = set(item.gold_source_doc_ids) | set(item.gold_triple_ids)
    if gold_ids & evidence_ids:
        return True
    text = " ".join([entry.content for entry in evidence] + sorted(evidence_ids))
    return _token_overlap(item.gold_evidence_text or item.gold_answer, text) >= 0.45


def _token_overlap(gold: str, observed: str) -> float:
    stopwords = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "are", "what", "which", "not"}
    gold_tokens = {token for token in re.findall(r"[a-z0-9._§:/-]+", gold.lower()) if token not in stopwords}
    observed_tokens = set(re.findall(r"[a-z0-9._§:/-]+", observed.lower()))
    if not gold_tokens:
        return 0.0
    return len(gold_tokens & observed_tokens) / len(gold_tokens)


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


def _confidence_analysis(
    items: list[AdversarialItem],
    computed_result: dict[str, object],
    classifier: ClassifierRouter,
) -> dict[str, object]:
    result_by_id = {row["id"]: row for row in computed_result["results"]}
    buckets = defaultdict(lambda: Counter(total=0, route_misses=0, answer_misses=0, evidence_misses=0))
    rows: list[dict[str, object]] = []
    for item in items:
        confidence = compute_route_confidence(item.query, classifier=classifier)
        result = result_by_id[item.id]
        label = str(confidence["confidence_label"])
        buckets[label]["total"] += 1
        buckets[label]["route_misses"] += int(not result["route_correct"])
        buckets[label]["answer_misses"] += int(not result["answer_correct"])
        buckets[label]["evidence_misses"] += int(not result["evidence_hit"])
        rows.append(
            {
                "id": item.id,
                "query": item.query,
                "split": item.split,
                "intended_route_family": item.intended_route_family,
                "ambiguity_tags": item.ambiguity_tags,
                "route_correct": result["route_correct"],
                "answer_correct": result["answer_correct"],
                "evidence_hit": result["evidence_hit"],
                **confidence,
            }
        )
    summary = {
        "total": len(rows),
        "bucket_summary": {
            label: {
                "total": counter["total"],
                "route_misses": counter["route_misses"],
                "answer_misses": counter["answer_misses"],
                "evidence_misses": counter["evidence_misses"],
                "route_miss_rate": counter["route_misses"] / counter["total"] if counter["total"] else 0.0,
                "answer_miss_rate": counter["answer_misses"] / counter["total"] if counter["total"] else 0.0,
                "evidence_miss_rate": counter["evidence_misses"] / counter["total"] if counter["total"] else 0.0,
            }
            for label, counter in sorted(buckets.items())
        },
        "correlation_statement": _confidence_statement(buckets),
        "lowest_confidence_examples": sorted(rows, key=lambda row: float(row["confidence_score"]))[:10],
    }
    return {"summary": summary, "rows": rows}


def _confidence_statement(buckets: dict[str, Counter[str]]) -> str:
    low = buckets.get("low", Counter())
    high = buckets.get("high", Counter())
    low_error = (low["route_misses"] + low["answer_misses"]) / low["total"] if low["total"] else 0.0
    high_error = (high["route_misses"] + high["answer_misses"]) / high["total"] if high["total"] else 0.0
    if low["total"] and low_error > high_error:
        return f"Low confidence is more error-prone on hard cases: low combined miss rate={low_error:.3f}, high combined miss rate={high_error:.3f}."
    if low["total"]:
        return f"Low confidence did not show a higher miss rate here: low combined miss rate={low_error:.3f}, high combined miss rate={high_error:.3f}."
    return "No low-confidence examples were produced; inspect hard benchmark margins manually."


def _ablation_analysis(
    items: list[AdversarialItem],
    documents: list[Document],
    triples: list[Triple],
    classifier: ClassifierRouter,
    seed: int,
) -> dict[str, object]:
    normal = _build_retrievers(documents, triples)
    no_rerank = _build_retrievers(documents, triples, semantic_rerank=False)
    public_lexical = _build_retrievers(documents, triples, public_lexical=True)
    public_graph_only = _build_retrievers(documents, load_public_structure_triples("public_graph"))
    demo_kg_only = _build_retrievers(documents, load_public_structure_triples("demo_kg"))
    structure_items = [item for item in items if item.intended_route_family in {"kg", "hybrid"}]
    rows = {
        "computed_ras": _evaluate_system("computed_ras", items, normal, classifier, seed),
        "computed_ras_no_semantic_rerank": _evaluate_system("computed_ras", items, no_rerank, classifier, seed),
        "computed_ras_public_lexical_arbitrated": _evaluate_system("computed_ras_public_arbitrated", items, public_lexical, classifier, seed),
        "computed_ras_demo_kg_structure_subset": _evaluate_system("computed_ras", structure_items, demo_kg_only, classifier, seed),
        "computed_ras_public_graph_structure_subset": _evaluate_system("computed_ras", structure_items, public_graph_only, classifier, seed),
        "computed_ras_mixed_structure_subset": _evaluate_system("computed_ras", structure_items, normal, classifier, seed),
    }
    return {
        "systems": {
            name: {
                "total": row["total"],
                "route_accuracy": row["route_accuracy"],
                "answer_accuracy": row["answer_accuracy"],
                "evidence_hit_at_k": row["evidence_hit_at_k"],
                "top1_evidence_hit": row["top1_evidence_hit"],
            }
            for name, row in rows.items()
        },
        "interpretation": _ablation_interpretation(rows),
    }


def _ablation_interpretation(rows: dict[str, dict[str, object]]) -> list[str]:
    normal = rows["computed_ras"]
    no_rerank = rows["computed_ras_no_semantic_rerank"]
    public_lexical = rows["computed_ras_public_lexical_arbitrated"]
    public_graph = rows["computed_ras_public_graph_structure_subset"]
    mixed = rows["computed_ras_mixed_structure_subset"]
    return [
        f"Semantic rerank delta: no_rerank answer accuracy {no_rerank['answer_accuracy']:.3f} vs normal {normal['answer_accuracy']:.3f}.",
        f"Public lexical arbitration delta: arbitrated answer accuracy {public_lexical['answer_accuracy']:.3f} vs normal {normal['answer_accuracy']:.3f}.",
        f"Structure subset public_graph answer accuracy {public_graph['answer_accuracy']:.3f} vs mixed {mixed['answer_accuracy']:.3f}.",
    ]


def _strongest_fixed(results: dict[str, dict[str, object]]) -> dict[str, object]:
    fixed = {name: row for name, row in results.items() if name.startswith("always_")}
    winner = max(fixed, key=lambda name: fixed[name]["answer_accuracy"])
    return {"system": winner, "answer_accuracy": fixed[winner]["answer_accuracy"], "route_accuracy": fixed[winner]["route_accuracy"]}


def _takeaways(
    split_runs: dict[str, dict[str, dict[str, object]]],
    combined_runs: dict[str, dict[str, object]],
    confidence_payload: dict[str, object],
    ablation_payload: dict[str, object],
) -> list[str]:
    computed = combined_runs["computed_ras"]
    strongest = _strongest_fixed(combined_runs)
    weakest_tag = _weakest_tag(computed["per_ambiguity_tag"])
    rows = [
        f"Computed RAS hard-benchmark route accuracy is {computed['route_accuracy']:.3f}; answer accuracy is {computed['answer_accuracy']:.3f}.",
        f"Strongest fixed backend is {strongest['system']} at answer accuracy {strongest['answer_accuracy']:.3f}.",
        f"Weakest ambiguity tag for computed RAS is {weakest_tag}.",
        confidence_payload["summary"]["correlation_statement"],
    ]
    rows.extend(ablation_payload["interpretation"])
    for split in ("dev", "test"):
        row = split_runs[split]["computed_ras"]
        rows.append(f"{split}: computed RAS answer accuracy {row['answer_accuracy']:.3f}; evidence hit@k {row['evidence_hit_at_k']:.3f}.")
    return rows


def _weakest_tag(per_tag: dict[str, dict[str, object]]) -> str:
    if not per_tag:
        return "none"
    return min(per_tag, key=lambda tag: float(per_tag[tag]["answer_accuracy"]))


def _threats_to_validity() -> list[str]:
    return [
        "Hard cases are hand-constructed and source-selected, so they diagnose stress behavior rather than estimate real-world prevalence.",
        "The benchmark is intentionally small and adversarial; scores should not be compared directly to clean curated benchmark scores.",
        "Some examples are grounded in compact local/public artifacts, not broad web-scale evidence.",
        "Answer matching is normalized string matching rather than human evaluation.",
        "A baseline may win on a subtype because the subtype is intentionally route-boundary-heavy.",
    ]


def _write_csv(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "scope",
                "split",
                "system",
                "total",
                "route_accuracy",
                "answer_accuracy",
                "evidence_hit_at_k",
                "top1_evidence_hit",
                "top1_topk_gap_rate",
                "predicted_backend_distribution",
            ],
        )
        writer.writeheader()
        for split, systems in payload["systems"]["splits"].items():
            for system, row in systems.items():
                writer.writerow({"scope": "split", "split": split, "system": system, **_csv_metrics(row)})
        for system, row in payload["systems"]["combined"].items():
            writer.writerow({"scope": "combined", "split": "all", "system": system, **_csv_metrics(row)})


def _csv_metrics(row: dict[str, object]) -> dict[str, object]:
    return {
        "total": row["total"],
        "route_accuracy": row["route_accuracy"],
        "answer_accuracy": row["answer_accuracy"],
        "evidence_hit_at_k": row["evidence_hit_at_k"],
        "top1_evidence_hit": row["top1_evidence_hit"],
        "top1_topk_gap_rate": row["top1_topk_gap_rate"],
        "predicted_backend_distribution": row["predicted_backend_distribution"],
    }


def _markdown(payload: dict[str, object]) -> str:
    combined = payload["systems"]["combined"]
    lines = [
        "# Adversarial Hard-Case Evaluation",
        "",
        "This suite is intentionally harder than the clean curated/public benchmarks. It targets route-boundary ambiguity, near-miss evidence, and misleading exact terms.",
        "",
        f"Benchmark path: `{payload['benchmark']['path']}`.",
        f"Benchmark total: {payload['benchmark']['total']}.",
        f"Benchmark counts: {payload['benchmark']['counts']}.",
        f"Retrieval context: {payload['retrieval_context']}.",
        "",
        "## Combined Results",
        "",
        "| System | Route accuracy | Answer accuracy | Evidence hit@k | Top-1 evidence hit |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for system in ALL_SYSTEMS:
        row = combined[system]
        lines.append(f"| {system} | {row['route_accuracy']:.3f} | {row['answer_accuracy']:.3f} | {row['evidence_hit_at_k']:.3f} | {row['top1_evidence_hit']:.3f} |")
    lines.extend(
        [
            "",
            "## Computed RAS By Ambiguity Tag",
            "",
        ]
    )
    for tag, row in combined["computed_ras"]["per_ambiguity_tag"].items():
        lines.append(
            f"- {tag}: answer={row['answer_accuracy']:.3f}, route={row['route_accuracy']:.3f}, "
            f"evidence_hit@k={row['evidence_hit_at_k']:.3f}, top1={row['top1_evidence_hit']:.3f}."
        )
    lines.extend(
        [
            "",
            "## Strongest Fixed Backend",
            "",
            f"- {payload['strongest_fixed_backend']['system']} at answer accuracy {payload['strongest_fixed_backend']['answer_accuracy']:.3f}.",
            "",
            "## Takeaways",
            "",
            *[f"- {item}" for item in payload["takeaways"]],
            "",
            "## Threats To Validity",
            "",
            *[f"- {item}" for item in payload["threats_to_validity"]],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{JSON_PATH}`",
            f"- CSV: `{CSV_PATH}`",
            f"- Markdown: `{MARKDOWN_PATH}`",
            f"- Confidence JSON: `{CONFIDENCE_JSON_PATH}`",
            f"- Confidence Markdown: `{CONFIDENCE_MARKDOWN_PATH}`",
            f"- Ablation Markdown: `{ABLATION_MARKDOWN_PATH}`",
            f"- Plot: `{BASELINE_PLOT}`",
            f"- Plot: `{CONFIDENCE_PLOT}`",
            f"- Plot: `{TOPK_PLOT}`",
            "",
        ]
    )
    return "\n".join(lines)


def _confidence_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Adversarial Route Confidence",
        "",
        "Confidence uses computed RAS margin plus agreement with keyword and classifier routers.",
        "",
        f"Total examples: {summary['total']}.",
        f"Correlation statement: {summary['correlation_statement']}",
        "",
        "| Confidence | Total | Route miss rate | Answer miss rate | Evidence miss rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, row in summary["bucket_summary"].items():
        lines.append(
            f"| {label} | {row['total']} | {row['route_miss_rate']:.3f} | {row['answer_miss_rate']:.3f} | {row['evidence_miss_rate']:.3f} |"
        )
    lines.extend(["", "## Lowest-Confidence Examples", ""])
    for row in summary["lowest_confidence_examples"]:
        lines.append(
            f"- `{row['id']}` {row['selected_backend']} vs {row['top_competing_backend']}; "
            f"label={row['confidence_label']}, score={row['confidence_score']}, query={row['query']}"
        )
    lines.append("")
    return "\n".join(lines)


def _ablation_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Adversarial Ablation Summary",
        "",
        "| Variant | Total | Route accuracy | Answer accuracy | Evidence hit@k |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in payload["systems"].items():
        lines.append(f"| {name} | {row['total']} | {row['route_accuracy']:.3f} | {row['answer_accuracy']:.3f} | {row['evidence_hit_at_k']:.3f} |")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in payload["interpretation"])
    lines.append("")
    return "\n".join(lines)


def _matplotlib_pyplot():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib_cache")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_baselines_by_tag(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    combined = payload["systems"]["combined"]
    tags = sorted(combined["computed_ras"]["per_ambiguity_tag"])
    systems = ["computed_ras", payload["strongest_fixed_backend"]["system"]]
    x_positions = list(range(len(tags)))
    width = 0.38
    _, ax = plt.subplots(figsize=(12, 5))
    for idx, system in enumerate(systems):
        values = [combined[system]["per_ambiguity_tag"].get(tag, {"answer_accuracy": 0.0})["answer_accuracy"] for tag in tags]
        offsets = [x + (idx - 0.5) * width for x in x_positions]
        ax.bar(offsets, values, width, label=system)
    ax.set_title("Hard benchmark answer accuracy by ambiguity tag")
    ax.set_ylabel("Answer accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x_positions, tags, rotation=35, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_confidence(confidence_payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    order = ["low", "medium", "high"]
    summary = confidence_payload["summary"]["bucket_summary"]
    values = [
        summary.get(label, {}).get("answer_miss_rate", 0.0) + summary.get(label, {}).get("route_miss_rate", 0.0)
        for label in order
    ]
    _, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(order, values, color=["#c53030", "#d69e2e", "#2f855a"])
    ax.set_title("Adversarial confidence bucket combined miss rate")
    ax.set_ylabel("Route miss rate + answer miss rate")
    ax.set_ylim(0, max(1.0, max(values, default=0.0) + 0.1))
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_top1_topk(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    per_family = payload["systems"]["combined"]["computed_ras"]["per_family"]
    families = sorted(per_family)
    top1 = [per_family[family]["top1_evidence_hit"] for family in families]
    topk = [per_family[family]["evidence_hit_at_k"] for family in families]
    x_positions = list(range(len(families)))
    _, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar([x - 0.18 for x in x_positions], top1, 0.36, label="top-1")
    ax.bar([x + 0.18 for x in x_positions], topk, 0.36, label="top-k")
    ax.set_title("Computed RAS top-1 vs top-k evidence hit")
    ax.set_ylabel("Evidence hit rate")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x_positions, families)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PRISM on hard ambiguity/adversarial benchmark.")
    parser.add_argument("--seed", type=int, default=53)
    args = parser.parse_args()
    payload = verify_adversarial(seed=args.seed)
    computed = payload["systems"]["combined"]["computed_ras"]
    print(
        "adversarial_eval "
        f"benchmark_total={payload['benchmark']['total']} "
        f"route_accuracy={computed['route_accuracy']:.3f} "
        f"answer_accuracy={computed['answer_accuracy']:.3f} "
        f"evidence_hit_at_k={computed['evidence_hit_at_k']:.3f} "
        f"json={JSON_PATH} csv={CSV_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["takeaways"]:
        print(item)


if __name__ == "__main__":
    main()
