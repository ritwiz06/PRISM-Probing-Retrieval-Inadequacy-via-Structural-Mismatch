from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

from prism.human_eval.compare_annotations import load_comparative_annotations
from prism.llm_experiments.llm_router import LLMRouter
from prism.utils import write_json

HUMAN_EVAL_DIR = Path("data/human_eval")
COMPARATIVE_PACKET_JSON = HUMAN_EVAL_DIR / "comparative_packet.json"
COMPARATIVE_SUMMARY_JSON = HUMAN_EVAL_DIR / "comparative_summary.json"
LLM_VS_HUMAN_JSON = HUMAN_EVAL_DIR / "llm_vs_human_summary.json"
LLM_VS_HUMAN_MD = HUMAN_EVAL_DIR / "llm_vs_human_summary.md"


def compare_llm_to_human_eval(router: LLMRouter | None = None) -> dict[str, object]:
    active_router = router or LLMRouter()
    packet = _read_json(COMPARATIVE_PACKET_JSON, {"items": []})
    annotations = load_comparative_annotations()
    majority_by_item = _majority_preferences(annotations)
    diagnostics = active_router.diagnostics()
    if not diagnostics.get("available"):
        payload = {
            "status": "llm_unavailable",
            "llm_runtime": diagnostics,
            "packet_size": len(packet.get("items", [])),
            "annotation_count": len(annotations),
            "alignment": {},
            "interpretation": "No local LLM route choices were available, so human alignment is reported as pending.",
            "setup_note": _setup_note(diagnostics),
        }
        write_json(LLM_VS_HUMAN_JSON, payload)
        LLM_VS_HUMAN_MD.write_text(_markdown(payload), encoding="utf-8")
        return payload

    counters = Counter(total=0, aligned_with_preferred_route=0, unavailable=0)
    by_pair = defaultdict(lambda: Counter(total=0, aligned_with_preferred_route=0, unavailable=0))
    examples: list[dict[str, object]] = []
    for item in packet.get("items", []):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("comparative_item_id", ""))
        majority = majority_by_item.get(item_id, "Tie")
        preferred_output = _preferred_output(item, majority)
        prediction = active_router.predict(str(item.get("query", "")))
        pair = f"{item.get('system_a_label')}_vs_{item.get('system_b_label')}"
        aligned = prediction.available and preferred_output and prediction.route == preferred_output.get("route")
        counters["total"] += 1
        counters["aligned_with_preferred_route"] += int(bool(aligned))
        counters["unavailable"] += int(not prediction.available)
        by_pair[pair]["total"] += 1
        by_pair[pair]["aligned_with_preferred_route"] += int(bool(aligned))
        by_pair[pair]["unavailable"] += int(not prediction.available)
        examples.append(
            {
                "comparative_item_id": item_id,
                "query": item.get("query"),
                "system_pair": pair,
                "human_majority": majority,
                "preferred_route": preferred_output.get("route") if preferred_output else "",
                "llm_route": prediction.route,
                "llm_confidence": prediction.confidence,
                "aligned_with_preferred_route": bool(aligned),
            }
        )
    payload = {
        "status": "llm_alignment_evaluated",
        "llm_runtime": diagnostics,
        "packet_size": len(packet.get("items", [])),
        "annotation_count": len(annotations),
        "alignment": _counter_summary(counters),
        "by_system_pair": {pair: _counter_summary(counts) for pair, counts in sorted(by_pair.items())},
        "examples": examples,
        "interpretation": "Alignment compares LLM route choice to the route used by the human-majority preferred system output; it is approximate and does not re-annotate LLM text.",
    }
    write_json(LLM_VS_HUMAN_JSON, payload)
    LLM_VS_HUMAN_MD.write_text(_markdown(payload), encoding="utf-8")
    return payload


def _majority_preferences(annotations: list[object]) -> dict[str, str]:
    by_item: dict[str, Counter[str]] = defaultdict(Counter)
    for row in annotations:
        by_item[row.comparative_item_id][row.choices.get("overall_preference", "Tie")] += 1
    return {item_id: counts.most_common(1)[0][0] if counts else "Tie" for item_id, counts in by_item.items()}


def _preferred_output(item: dict[str, object], majority: str) -> dict[str, object]:
    if majority == "A":
        return item.get("system_a", {}) if isinstance(item.get("system_a"), dict) else {}
    if majority == "B":
        return item.get("system_b", {}) if isinstance(item.get("system_b"), dict) else {}
    return {}


def _counter_summary(counter: Counter[str]) -> dict[str, object]:
    total = counter["total"]
    return {
        "total": total,
        "aligned_with_preferred_route": counter["aligned_with_preferred_route"],
        "unavailable": counter["unavailable"],
        "alignment_rate": counter["aligned_with_preferred_route"] / total if total else 0.0,
    }


def _read_json(path: Path, default: dict[str, object]) -> dict[str, object]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _setup_note(diagnostics: dict[str, object]) -> str:
    return (
        "Local LLM runtime was unavailable. Start Ollama locally and set PRISM_LLM_MODEL if needed, "
        f"then rerun `python -m prism.llm_experiments.verify_llm_router`. Error: {diagnostics.get('error', '')}"
    )


def _markdown(payload: dict[str, object]) -> str:
    lines = ["# LLM Vs Human-Eval Summary", ""]
    lines.append(f"Status: `{payload['status']}`.")
    runtime = payload.get("llm_runtime", {})
    if isinstance(runtime, dict):
        lines.append(f"LLM provider/model: `{runtime.get('provider')}` / `{runtime.get('model')}`.")
        lines.append(f"Available: `{runtime.get('available')}`.")
    lines.extend(["", "## Alignment"])
    alignment = payload.get("alignment", {})
    if alignment:
        lines.append(f"- Alignment rate: {alignment.get('alignment_rate')}")
        lines.append(f"- Aligned examples: {alignment.get('aligned_with_preferred_route')} / {alignment.get('total')}")
    else:
        lines.append("- LLM alignment could not be computed because the local LLM was unavailable.")
    if payload.get("setup_note"):
        lines.extend(["", "## Setup Note", str(payload["setup_note"])])
    lines.extend(
        [
            "",
            "## Caveat",
            "This comparison maps LLM route choices to human-majority preferred system routes. It is useful for routing alignment, but it is not a direct human judgment of LLM-generated answers.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    payload = compare_llm_to_human_eval()
    print(f"llm_vs_human status={payload['status']} summary={LLM_VS_HUMAN_MD}")

