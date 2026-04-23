from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from prism.adversarial.loaders import load_adversarial_benchmark
from prism.analysis.evaluation import answer_matches_gold, load_combined_benchmark
from prism.app.pipeline import answer_query, load_retrievers
from prism.calibration.route_calibrator import CalibratorConfig, RouteCalibrator
from prism.external_benchmarks.loaders import load_external_mini_benchmark
from prism.generalization.loaders import load_generalization_benchmark
from prism.public_corpus.loaders import load_public_benchmark
from prism.router_baselines.classifier_router import ClassifierRouter
from prism.utils import read_json, write_json

PACKET_DIR = Path("data/human_eval")
PACKET_JSON = PACKET_DIR / "eval_packet.json"
PACKET_CSV = PACKET_DIR / "eval_packet.csv"
PACKET_MD = PACKET_DIR / "eval_packet.md"

ROUTE_FAMILIES = ("bm25", "dense", "kg", "hybrid")


@dataclass(frozen=True, slots=True)
class CandidateExample:
    stable_id: str
    benchmark_source: str
    query: str
    gold_route: str
    gold_answer: str
    difficulty: str
    gold_evidence: list[str]
    notes: str = ""
    system_variant: str = "computed_ras"


@dataclass(frozen=True, slots=True)
class HumanEvalItem:
    item_id: str
    benchmark_source: str
    system_variant: str
    query: str
    gold_route: str
    predicted_route: str
    selected_backend: str
    final_answer: str
    automatic_correct: bool
    gold_answer: str
    evidence_ids: list[str]
    evidence_snippets: list[str]
    reasoning_trace: list[dict[str, object]]
    route_rationale: str
    route_family: str
    difficulty: str
    packet_notes: str


def build_eval_packet(target_size: int = 36) -> dict[str, object]:
    """Build a deterministic human-eval packet from existing PRISM benchmarks."""

    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    normal_candidates = _select_balanced_candidates()
    calibrated_candidates = _select_calibrated_adversarial_candidates(limit=max(0, target_size - len(normal_candidates)))
    candidates = normal_candidates + calibrated_candidates
    retrievers = load_retrievers()
    classifier = _train_classifier()
    calibrator = _load_calibrator(classifier)
    items: list[HumanEvalItem] = []
    for index, candidate in enumerate(candidates[:target_size], start=1):
        backend_override = None
        variant_note = ""
        if candidate.system_variant == "calibrated_ras":
            decision = calibrator.predict(candidate.query)
            backend_override = decision.selected_backend
            variant_note = f"Calibrated route from {decision.original_backend} to {decision.selected_backend}; {decision.rationale}"
        payload = answer_query(candidate.query, top_k=5, retrievers=retrievers, backend_override=backend_override)
        answer = payload["answer"]
        predicted = str(payload["selected_backend"])
        final_answer = str(answer["final_answer"])
        item_id = f"he_{index:03d}_{candidate.stable_id}_{candidate.system_variant}"
        evidence_ids = [str(row["item_id"]) for row in payload["top_evidence"]]
        evidence_snippets = [_snippet(str(row["content"])) for row in payload["top_evidence"]]
        automatic_correct = answer_matches_gold(final_answer, candidate.gold_answer)
        route_rationale = str(answer.get("route_rationale") or variant_note or "Computed RAS route rationale unavailable.")
        if variant_note:
            route_rationale = f"{variant_note} Production answer rationale: {route_rationale}"
        items.append(
            HumanEvalItem(
                item_id=item_id,
                benchmark_source=candidate.benchmark_source,
                system_variant=candidate.system_variant,
                query=candidate.query,
                gold_route=candidate.gold_route,
                predicted_route=predicted,
                selected_backend=predicted,
                final_answer=final_answer,
                automatic_correct=automatic_correct,
                gold_answer=candidate.gold_answer,
                evidence_ids=evidence_ids,
                evidence_snippets=evidence_snippets,
                reasoning_trace=list(payload["reasoning_trace"]),
                route_rationale=route_rationale,
                route_family=candidate.gold_route,
                difficulty=candidate.difficulty,
                packet_notes="; ".join(part for part in [candidate.notes, variant_note] if part),
            )
        )
    payload_out = {
        "packet_version": "2026-04-20",
        "packet_size": len(items),
        "sampling_protocol": (
            "Deterministic balanced packet: curated, generalization_v2, public_raw, and adversarial examples, "
            "with calibrated adversarial variants included for rescue-path auditing."
        ),
        "counts": packet_counts(items),
        "items": [asdict(item) for item in items],
    }
    write_json(PACKET_JSON, payload_out)
    _write_packet_csv(PACKET_CSV, items)
    PACKET_MD.write_text(_packet_markdown(payload_out), encoding="utf-8")
    return payload_out


def packet_counts(items: list[HumanEvalItem]) -> dict[str, dict[str, int]]:
    keys = ("benchmark_source", "route_family", "difficulty", "system_variant", "automatic_correct")
    counts: dict[str, dict[str, int]] = {key: {} for key in keys}
    for item in items:
        values = {
            "benchmark_source": item.benchmark_source,
            "route_family": item.route_family,
            "difficulty": item.difficulty,
            "system_variant": item.system_variant,
            "automatic_correct": str(item.automatic_correct),
        }
        for key, value in values.items():
            counts[key][value] = counts[key].get(value, 0) + 1
    return {key: dict(sorted(value.items())) for key, value in counts.items()}


def _select_balanced_candidates() -> list[CandidateExample]:
    return (
        _take_by_family(_curated_candidates(), per_family=2)
        + _take_by_family(_generalization_candidates(), per_family=2)
        + _take_by_family(_public_candidates(), per_family=2)
        + _take_by_family(_adversarial_candidates(), per_family=2)
    )


def _select_calibrated_adversarial_candidates(limit: int) -> list[CandidateExample]:
    if limit <= 0:
        return []
    rows = _adversarial_candidates()
    picked = _take_by_family(rows, per_family=1)
    return [
        CandidateExample(
            stable_id=candidate.stable_id,
            benchmark_source=candidate.benchmark_source,
            query=candidate.query,
            gold_route=candidate.gold_route,
            gold_answer=candidate.gold_answer,
            difficulty=candidate.difficulty,
            gold_evidence=candidate.gold_evidence,
            notes=f"Calibrated duplicate for comparison. {candidate.notes}",
            system_variant="calibrated_ras",
        )
        for candidate in picked[:limit]
    ]


def _take_by_family(candidates: Iterable[CandidateExample], per_family: int) -> list[CandidateExample]:
    by_family = {family: [] for family in ROUTE_FAMILIES}
    for candidate in candidates:
        if candidate.gold_route in by_family and len(by_family[candidate.gold_route]) < per_family:
            by_family[candidate.gold_route].append(candidate)
    selected: list[CandidateExample] = []
    for family in ROUTE_FAMILIES:
        selected.extend(by_family[family])
    return selected


def _curated_candidates() -> list[CandidateExample]:
    rows = []
    for index, row in enumerate(load_combined_benchmark()):
        rows.append(
            CandidateExample(
                stable_id=f"curated_{index:03d}",
                benchmark_source="curated",
                query=str(row["query"]),
                gold_route=str(row["gold_route"]),
                gold_answer=str(row["gold_answer"]),
                difficulty="easy_curated",
                gold_evidence=[str(value) for value in row.get("gold_evidence_ids", [])],
                notes=f"Curated slice={row.get('slice')}.",
            )
        )
    return rows


def _generalization_candidates() -> list[CandidateExample]:
    rows = []
    for item in load_generalization_benchmark(split="test"):
        rows.append(
            CandidateExample(
                stable_id=item.id,
                benchmark_source="generalization_v2",
                query=item.query,
                gold_route=item.route_family,
                gold_answer=item.gold_answer,
                difficulty=item.difficulty or "held_out",
                gold_evidence=[item.gold_evidence_text] if item.gold_evidence_text else [],
                notes=f"source={item.source_dataset}; tag={item.tag}; {item.notes}",
            )
        )
    return rows


def _public_candidates() -> list[CandidateExample]:
    rows = []
    for item in load_public_benchmark(split="test"):
        rows.append(
            CandidateExample(
                stable_id=item.id,
                benchmark_source="public_raw",
                query=item.query,
                gold_route=item.route_family,
                gold_answer=item.gold_answer,
                difficulty=item.difficulty,
                gold_evidence=item.gold_source_doc_ids,
                notes=f"source_style={item.source_dataset_style}; {item.notes}",
            )
        )
    return rows


def _adversarial_candidates() -> list[CandidateExample]:
    rows = []
    for item in load_adversarial_benchmark(split="test"):
        rows.append(
            CandidateExample(
                stable_id=item.id,
                benchmark_source="adversarial",
                query=item.query,
                gold_route=item.intended_route_family,
                gold_answer=item.gold_answer,
                difficulty=item.difficulty,
                gold_evidence=item.gold_source_doc_ids + item.gold_triple_ids,
                notes=f"tags={','.join(item.ambiguity_tags)}; {item.notes}",
            )
        )
    return rows


def _train_classifier() -> ClassifierRouter:
    rows = load_combined_benchmark()
    return ClassifierRouter(seed=53).fit([str(row["query"]) for row in rows], [str(row["gold_route"]) for row in rows])


def _load_calibrator(classifier: ClassifierRouter) -> RouteCalibrator:
    config_path = Path("data/eval/calibrated_dev_tuning.json")
    if config_path.exists():
        payload = read_json(config_path)
        return RouteCalibrator(CalibratorConfig(**payload["selected_config"]), classifier=classifier)
    return RouteCalibrator(classifier=classifier)


def _write_packet_csv(path: Path, items: list[HumanEvalItem]) -> None:
    import csv

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "item_id",
                "benchmark_source",
                "system_variant",
                "route_family",
                "difficulty",
                "query",
                "gold_route",
                "predicted_route",
                "automatic_correct",
                "gold_answer",
                "final_answer",
                "evidence_ids",
                "evidence_snippets",
                "route_rationale",
                "packet_notes",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "item_id": item.item_id,
                    "benchmark_source": item.benchmark_source,
                    "system_variant": item.system_variant,
                    "route_family": item.route_family,
                    "difficulty": item.difficulty,
                    "query": item.query,
                    "gold_route": item.gold_route,
                    "predicted_route": item.predicted_route,
                    "automatic_correct": item.automatic_correct,
                    "gold_answer": item.gold_answer,
                    "final_answer": item.final_answer,
                    "evidence_ids": " | ".join(item.evidence_ids),
                    "evidence_snippets": " || ".join(item.evidence_snippets),
                    "route_rationale": item.route_rationale,
                    "packet_notes": item.packet_notes,
                }
            )


def _packet_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# PRISM Human Evaluation Packet",
        "",
        f"Packet size: {payload['packet_size']}.",
        f"Sampling protocol: {payload['sampling_protocol']}",
        f"Counts: `{payload['counts']}`.",
        "",
        "## Items",
        "",
    ]
    for item in payload["items"]:
        lines.extend(
            [
                f"### {item['item_id']}",
                "",
                f"- Benchmark: `{item['benchmark_source']}`",
                f"- Variant: `{item['system_variant']}`",
                f"- Route family: `{item['route_family']}`; predicted `{item['predicted_route']}`",
                f"- Automatic correct: `{item['automatic_correct']}`",
                f"- Query: {item['query']}",
                f"- Gold answer: {item['gold_answer']}",
                f"- Final answer: {item['final_answer']}",
                f"- Evidence ids: `{', '.join(item['evidence_ids'])}`",
                f"- Evidence snippets: {' / '.join(item['evidence_snippets'][:2])}",
                f"- Route rationale: {item['route_rationale']}",
                "",
            ]
        )
    return "\n".join(lines)


def _snippet(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."
