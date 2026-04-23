from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from prism.analysis.evaluation import answer_matches_gold, load_combined_benchmark
from prism.answering.generator import synthesize_answer
from prism.app.pipeline import load_retrievers
from prism.calibration.route_calibrator import CalibratorConfig, RouteCalibrator
from prism.calibration.topk_rescue import rescue_topk_evidence
from prism.generalization.loaders import load_generalization_benchmark
from prism.human_eval.sample_builder import _snippet
from prism.public_corpus.loaders import load_public_benchmark
from prism.adversarial.loaders import load_adversarial_benchmark
from prism.ras.compute_ras import route_query
from prism.router_baselines.classifier_router import ClassifierRouter
from prism.schemas import RetrievedItem
from prism.utils import read_json, write_json

HUMAN_EVAL_DIR = Path("data/human_eval")
COMPARATIVE_PACKET_JSON = HUMAN_EVAL_DIR / "comparative_packet.json"
COMPARATIVE_PACKET_CSV = HUMAN_EVAL_DIR / "comparative_packet.csv"
COMPARATIVE_PACKET_MD = HUMAN_EVAL_DIR / "comparative_packet.md"

ROUTE_FAMILIES = ("bm25", "dense", "kg", "hybrid")


@dataclass(frozen=True, slots=True)
class ComparativeCandidate:
    stable_id: str
    benchmark_source: str
    query: str
    gold_route: str
    gold_answer: str
    route_family: str
    difficulty: str
    notes: str
    ambiguity_tags: list[str]


@dataclass(frozen=True, slots=True)
class SystemOutput:
    system_label: str
    route: str
    selected_backend: str
    final_answer: str
    automatic_correct: bool
    evidence_ids: list[str]
    evidence_snippets: list[str]
    reasoning_trace: list[dict[str, object]]
    route_rationale: str
    rescue_metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class ComparativeItem:
    comparative_item_id: str
    source_benchmark: str
    query: str
    route_family: str
    difficulty: str
    ambiguity_tags: list[str]
    system_a_label: str
    system_b_label: str
    system_a: SystemOutput
    system_b: SystemOutput
    gold_answer: str
    gold_route: str
    comparison_tag: str
    selection_reason: str


def build_comparative_packet(target_size: int = 28, seed: int = 53) -> dict[str, object]:
    """Build a deterministic side-by-side packet for human comparison."""

    HUMAN_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    classifier = _train_classifier(seed)
    calibrator = _load_calibrator(classifier)
    retrievers = load_retrievers()
    pairs = _comparison_plan(target_size)
    items: list[ComparativeItem] = []
    for index, (candidate, system_b_label, base_tag) in enumerate(pairs[:target_size], start=1):
        system_a = _run_system(
            candidate.query,
            candidate.gold_answer,
            "computed_ras",
            retrievers,
            classifier,
            calibrator,
        )
        system_b = _run_system(
            candidate.query,
            candidate.gold_answer,
            system_b_label,
            retrievers,
            classifier,
            calibrator,
        )
        comparison_tag = _comparison_tag(base_tag, system_a, system_b, candidate.query)
        items.append(
            ComparativeItem(
                comparative_item_id=f"che_{index:03d}_{candidate.stable_id}_{_safe_label(system_b_label)}",
                source_benchmark=candidate.benchmark_source,
                query=candidate.query,
                route_family=candidate.route_family,
                difficulty=candidate.difficulty,
                ambiguity_tags=candidate.ambiguity_tags,
                system_a_label="computed_ras",
                system_b_label=system_b_label,
                system_a=system_a,
                system_b=system_b,
                gold_answer=candidate.gold_answer,
                gold_route=candidate.gold_route,
                comparison_tag=comparison_tag,
                selection_reason=_selection_reason(base_tag, comparison_tag, system_a, system_b, candidate),
            )
        )
    payload = {
        "packet_version": "2026-04-21",
        "packet_size": len(items),
        "sampling_protocol": (
            "Deterministic comparative packet focused on side-by-side disagreements and ambiguity-heavy cases. "
            "System A is normal computed RAS; System B is calibrated rescue, classifier routing, or a fixed backend."
        ),
        "counts": comparative_counts(items),
        "items": [asdict(item) for item in items],
    }
    write_json(COMPARATIVE_PACKET_JSON, payload)
    _write_comparative_csv(COMPARATIVE_PACKET_CSV, items)
    COMPARATIVE_PACKET_MD.write_text(_comparative_markdown(payload), encoding="utf-8")
    return payload


def comparative_counts(items: list[ComparativeItem]) -> dict[str, dict[str, int]]:
    counts = {
        "source_benchmark": {},
        "route_family": {},
        "system_pair": {},
        "comparison_tag": {},
        "difficulty": {},
    }
    for item in items:
        values = {
            "source_benchmark": item.source_benchmark,
            "route_family": item.route_family,
            "system_pair": f"{item.system_a_label}_vs_{item.system_b_label}",
            "comparison_tag": item.comparison_tag,
            "difficulty": item.difficulty,
        }
        for key, value in values.items():
            counts[key][value] = counts[key].get(value, 0) + 1
    return {key: dict(sorted(value.items())) for key, value in counts.items()}


def _comparison_plan(target_size: int) -> list[tuple[ComparativeCandidate, str, str]]:
    adversarial = _take_by_family(_adversarial_candidates(), per_family=3)
    public = _take_by_family(_public_candidates(), per_family=2)
    generalization = _take_by_family(_generalization_candidates(), per_family=2)
    curated = _take_by_family(_curated_candidates(), per_family=1)

    plan: list[tuple[ComparativeCandidate, str, str]] = []
    for candidate in adversarial[:8]:
        plan.append((candidate, "calibrated_rescue", "computed_vs_calibrated_rescue"))
    for candidate in adversarial[8:12]:
        plan.append((candidate, "classifier_router", "computed_vs_classifier_router"))
    for candidate in adversarial[:4]:
        plan.append((candidate, "always_dense", "computed_vs_strong_fixed_backend"))
    for candidate in public[:4]:
        plan.append((candidate, "always_bm25", "computed_vs_public_lexical_fixed_backend"))
    for candidate in generalization[:4]:
        plan.append((candidate, "classifier_router", "computed_vs_classifier_router"))
    for candidate in curated[:4]:
        plan.append((candidate, "classifier_router", "computed_vs_classifier_router"))
    if len(plan) < target_size:
        for candidate in public[4:] + generalization[4:] + curated[4:]:
            plan.append((candidate, _fixed_backend_for(candidate), "computed_vs_family_fixed_backend"))
            if len(plan) >= target_size:
                break
    return plan[:target_size]


def _run_system(
    query: str,
    gold_answer: str,
    system_label: str,
    retrievers: dict[str, object],
    classifier: ClassifierRouter,
    calibrator: RouteCalibrator,
) -> SystemOutput:
    decision = route_query(query)
    selected_backend = _selected_backend(system_label, query, decision.selected_backend, classifier, calibrator)
    evidence = retrievers[selected_backend].retrieve(query, top_k=5)
    rescue_metadata: dict[str, object] = {"applied": False, "system_label": system_label}
    if system_label == "calibrated_rescue":
        evidence, rescue_metadata = rescue_topk_evidence(query, evidence, selected_backend)
    answer = synthesize_answer(query, decision.features, decision.ras_scores, selected_backend, evidence)
    final_answer = answer.final_answer
    rationale = answer.route_rationale
    if system_label == "classifier_router":
        rationale = f"Classifier router selected {selected_backend}. Production RAS would select {decision.selected_backend}. {rationale}"
    elif system_label == "calibrated_rescue":
        calibrated = calibrator.predict(query)
        rationale = (
            f"Calibrated rescue selected {selected_backend} from computed RAS {calibrated.original_backend}; "
            f"{calibrated.rationale}; top-k rescue applied={rescue_metadata.get('applied')}. {rationale}"
        )
    elif system_label.startswith("always_"):
        rationale = f"Fixed-backend baseline forced {selected_backend}. Production RAS would select {decision.selected_backend}. {rationale}"
    return SystemOutput(
        system_label=system_label,
        route=selected_backend,
        selected_backend=selected_backend,
        final_answer=final_answer,
        automatic_correct=answer_matches_gold(final_answer, gold_answer),
        evidence_ids=[item.item_id for item in evidence],
        evidence_snippets=[_snippet(item.content) for item in evidence],
        reasoning_trace=list(answer.reasoning_trace_steps),
        route_rationale=rationale,
        rescue_metadata=rescue_metadata,
    )


def _selected_backend(
    system_label: str,
    query: str,
    computed_backend: str,
    classifier: ClassifierRouter,
    calibrator: RouteCalibrator,
) -> str:
    if system_label == "computed_ras":
        return computed_backend
    if system_label == "classifier_router":
        return classifier.predict(query).route
    if system_label == "calibrated_rescue":
        return calibrator.predict(query).selected_backend
    if system_label.startswith("always_"):
        return system_label.replace("always_", "")
    raise ValueError(f"Unsupported comparative system label: {system_label}")


def _comparison_tag(base_tag: str, system_a: SystemOutput, system_b: SystemOutput, query: str) -> str:
    route_disagrees = system_a.selected_backend != system_b.selected_backend
    correctness_disagrees = system_a.automatic_correct != system_b.automatic_correct
    low_confidence = _ras_margin(query) <= 0.15
    if correctness_disagrees:
        if not system_a.automatic_correct and system_b.automatic_correct:
            return f"{base_tag}:computed_miss_system_b_hit"
        if system_a.automatic_correct and not system_b.automatic_correct:
            return f"{base_tag}:computed_hit_system_b_miss"
    if route_disagrees:
        return f"{base_tag}:route_disagreement"
    if low_confidence:
        return f"{base_tag}:computed_low_confidence"
    return f"{base_tag}:trace_evidence_audit"


def _selection_reason(
    base_tag: str,
    comparison_tag: str,
    system_a: SystemOutput,
    system_b: SystemOutput,
    candidate: ComparativeCandidate,
) -> str:
    parts = [
        f"Selected for {base_tag}.",
        f"Resolved tag: {comparison_tag}.",
        f"Source={candidate.benchmark_source}; family={candidate.route_family}; difficulty={candidate.difficulty}.",
    ]
    if system_a.selected_backend != system_b.selected_backend:
        parts.append(f"Route disagreement: A={system_a.selected_backend}, B={system_b.selected_backend}.")
    if system_a.automatic_correct != system_b.automatic_correct:
        parts.append(f"Automatic correctness disagreement: A={system_a.automatic_correct}, B={system_b.automatic_correct}.")
    if candidate.ambiguity_tags:
        parts.append(f"Ambiguity tags: {', '.join(candidate.ambiguity_tags)}.")
    return " ".join(parts)


def _curated_candidates() -> list[ComparativeCandidate]:
    rows = []
    for index, row in enumerate(load_combined_benchmark()):
        rows.append(
            ComparativeCandidate(
                stable_id=f"curated_{index:03d}",
                benchmark_source="curated",
                query=str(row["query"]),
                gold_route=str(row["gold_route"]),
                gold_answer=str(row["gold_answer"]),
                route_family=str(row["gold_route"]),
                difficulty="easy_curated",
                notes=f"Curated slice={row.get('slice')}.",
                ambiguity_tags=[],
            )
        )
    return rows


def _generalization_candidates() -> list[ComparativeCandidate]:
    return [
        ComparativeCandidate(
            stable_id=item.id,
            benchmark_source="generalization_v2",
            query=item.query,
            gold_route=item.route_family,
            gold_answer=item.gold_answer,
            route_family=item.route_family,
            difficulty=item.difficulty or "held_out",
            notes=f"source={item.source_dataset}; tag={item.tag}; {item.notes}",
            ambiguity_tags=[item.tag] if item.tag else [],
        )
        for item in load_generalization_benchmark(split="test")
    ]


def _public_candidates() -> list[ComparativeCandidate]:
    return [
        ComparativeCandidate(
            stable_id=item.id,
            benchmark_source="public_raw",
            query=item.query,
            gold_route=item.route_family,
            gold_answer=item.gold_answer,
            route_family=item.route_family,
            difficulty=item.difficulty,
            notes=f"source_style={item.source_dataset_style}; {item.notes}",
            ambiguity_tags=[],
        )
        for item in load_public_benchmark(split="test")
    ]


def _adversarial_candidates() -> list[ComparativeCandidate]:
    return [
        ComparativeCandidate(
            stable_id=item.id,
            benchmark_source="adversarial",
            query=item.query,
            gold_route=item.intended_route_family,
            gold_answer=item.gold_answer,
            route_family=item.intended_route_family,
            difficulty=item.difficulty,
            notes=item.notes,
            ambiguity_tags=list(item.ambiguity_tags),
        )
        for item in load_adversarial_benchmark(split="test")
    ]


def _take_by_family(candidates: Iterable[ComparativeCandidate], per_family: int) -> list[ComparativeCandidate]:
    by_family = {family: [] for family in ROUTE_FAMILIES}
    for candidate in candidates:
        if candidate.route_family in by_family and len(by_family[candidate.route_family]) < per_family:
            by_family[candidate.route_family].append(candidate)
    selected: list[ComparativeCandidate] = []
    for index in range(per_family):
        for family in ROUTE_FAMILIES:
            if index < len(by_family[family]):
                selected.append(by_family[family][index])
    return selected


def _fixed_backend_for(candidate: ComparativeCandidate) -> str:
    if candidate.benchmark_source == "public_raw" and candidate.route_family == "bm25":
        return "always_bm25"
    if candidate.benchmark_source == "adversarial":
        return "always_dense"
    return f"always_{candidate.route_family}"


def _train_classifier(seed: int) -> ClassifierRouter:
    rows = load_combined_benchmark()
    return ClassifierRouter(seed=seed).fit([str(row["query"]) for row in rows], [str(row["gold_route"]) for row in rows])


def _load_calibrator(classifier: ClassifierRouter) -> RouteCalibrator:
    config_path = Path("data/eval/calibrated_dev_tuning.json")
    if config_path.exists():
        payload = read_json(config_path)
        return RouteCalibrator(CalibratorConfig(**payload["selected_config"]), classifier=classifier)
    return RouteCalibrator(classifier=classifier)


def _ras_margin(query: str) -> float:
    scores = sorted(route_query(query).ras_scores.values())
    if len(scores) < 2:
        return 1.0
    return float(scores[1] - scores[0])


def _safe_label(label: str) -> str:
    return label.replace(" ", "_").replace("/", "_")


def _write_comparative_csv(path: Path, items: list[ComparativeItem]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "comparative_item_id",
                "source_benchmark",
                "route_family",
                "difficulty",
                "query",
                "system_a_label",
                "system_a_route",
                "system_a_correct",
                "system_a_answer",
                "system_b_label",
                "system_b_route",
                "system_b_correct",
                "system_b_answer",
                "comparison_tag",
                "selection_reason",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "comparative_item_id": item.comparative_item_id,
                    "source_benchmark": item.source_benchmark,
                    "route_family": item.route_family,
                    "difficulty": item.difficulty,
                    "query": item.query,
                    "system_a_label": item.system_a_label,
                    "system_a_route": item.system_a.selected_backend,
                    "system_a_correct": item.system_a.automatic_correct,
                    "system_a_answer": item.system_a.final_answer,
                    "system_b_label": item.system_b_label,
                    "system_b_route": item.system_b.selected_backend,
                    "system_b_correct": item.system_b.automatic_correct,
                    "system_b_answer": item.system_b.final_answer,
                    "comparison_tag": item.comparison_tag,
                    "selection_reason": item.selection_reason,
                }
            )


def _comparative_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# PRISM Comparative Human Evaluation Packet",
        "",
        f"Packet size: {payload['packet_size']}.",
        f"Sampling protocol: {payload['sampling_protocol']}",
        f"Counts: `{payload['counts']}`.",
        "",
        "## Items",
        "",
    ]
    for item in payload["items"]:
        a = item["system_a"]
        b = item["system_b"]
        lines.extend(
            [
                f"### {item['comparative_item_id']}",
                "",
                f"- Source: `{item['source_benchmark']}`",
                f"- Route family: `{item['route_family']}`; difficulty `{item['difficulty']}`",
                f"- Comparison tag: `{item['comparison_tag']}`",
                f"- Query: {item['query']}",
                f"- Gold answer: {item['gold_answer']}",
                f"- Selection reason: {item['selection_reason']}",
                "",
                "#### System A",
                "",
                f"- Label: `{item['system_a_label']}`",
                f"- Backend: `{a['selected_backend']}`; automatic correct `{a['automatic_correct']}`",
                f"- Answer: {a['final_answer']}",
                f"- Evidence ids: `{', '.join(a['evidence_ids'])}`",
                f"- Evidence snippets: {' / '.join(a['evidence_snippets'][:2])}",
                f"- Route rationale: {a['route_rationale']}",
                "",
                "#### System B",
                "",
                f"- Label: `{item['system_b_label']}`",
                f"- Backend: `{b['selected_backend']}`; automatic correct `{b['automatic_correct']}`",
                f"- Answer: {b['final_answer']}",
                f"- Evidence ids: `{', '.join(b['evidence_ids'])}`",
                f"- Evidence snippets: {' / '.join(b['evidence_snippets'][:2])}",
                f"- Route rationale: {b['route_rationale']}",
                "",
            ]
        )
    return "\n".join(lines)
