from __future__ import annotations

import argparse
import os
from pathlib import Path

from prism.generalization.verify_generalization_v2 import JSON_PATH as GENERALIZATION_V2_JSON
from prism.generalization.verify_generalization_v2 import verify_generalization_v2
from prism.public_corpus.verify_public_corpus import JSON_PATH as PUBLIC_JSON
from prism.public_corpus.verify_public_corpus import verify_public_corpus
from prism.utils import read_json, write_json

JSON_PATH = Path("data/eval/public_vs_local_grounding.json")
MARKDOWN_PATH = Path("data/eval/public_vs_local_grounding_summary.md")
PLOT_PATH = Path("data/eval/public_vs_local_grounding_family_delta.png")


def compare_grounding() -> dict[str, object]:
    if not GENERALIZATION_V2_JSON.exists():
        verify_generalization_v2()
    if not PUBLIC_JSON.exists():
        verify_public_corpus()

    local = read_json(GENERALIZATION_V2_JSON)
    public = read_json(PUBLIC_JSON)
    local_test = _local_test_result(local)
    public_test = public["systems"]["test"]["computed_ras"]
    family_delta = _family_delta(local_test["per_family"], public_test["per_family"])
    payload = {
        "local_normalized_source": str(GENERALIZATION_V2_JSON),
        "public_raw_source": str(PUBLIC_JSON),
        "local_normalized_test_answer_accuracy": local_test["answer_accuracy"],
        "public_raw_test_answer_accuracy": public_test["answer_accuracy"],
        "overall_answer_accuracy_delta": public_test["answer_accuracy"] - local_test["answer_accuracy"],
        "local_normalized_test_route_accuracy": local_test["route_accuracy"],
        "public_raw_test_route_accuracy": public_test["route_accuracy"],
        "overall_route_accuracy_delta": public_test["route_accuracy"] - local_test["route_accuracy"],
        "per_family_delta": family_delta,
        "diagnosis": _diagnosis(local_test, public_test, family_delta),
        "threats_to_validity": [
            "The local-normalized benchmark and public raw benchmark are different suites, so deltas are directional rather than paired-example effects.",
            "Public raw documents can be fetched, cached, or fallback snapshots depending on network availability.",
            "The public benchmark remains small and source-selected.",
            "Deductive and relational public results still use the compact demo KG for structured evidence.",
        ],
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(JSON_PATH, payload)
    MARKDOWN_PATH.write_text(_markdown(payload), encoding="utf-8")
    _plot_family_delta(payload, PLOT_PATH)
    return payload


def _local_test_result(payload: dict[str, object]) -> dict[str, object]:
    if "clean" in payload["systems"] and "test" in payload["systems"]["clean"]:
        return payload["systems"]["clean"]["test"]["computed_ras"]
    first_mode = next(iter(payload["systems"]))
    first_split = "test" if "test" in payload["systems"][first_mode] else next(iter(payload["systems"][first_mode]))
    return payload["systems"][first_mode][first_split]["computed_ras"]


def _family_delta(local_per_family: dict[str, object], public_per_family: dict[str, object]) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for family in sorted(set(local_per_family) | set(public_per_family)):
        local_answer = float(local_per_family.get(family, {}).get("answer_accuracy", 0.0))
        public_answer = float(public_per_family.get(family, {}).get("answer_accuracy", 0.0))
        local_route = float(local_per_family.get(family, {}).get("route_accuracy", 0.0))
        public_route = float(public_per_family.get(family, {}).get("route_accuracy", 0.0))
        local_evidence = float(local_per_family.get(family, {}).get("evidence_hit_at_k", local_answer))
        public_evidence = float(public_per_family.get(family, {}).get("evidence_hit_at_k", public_answer))
        rows[family] = {
            "local_answer_accuracy": local_answer,
            "public_answer_accuracy": public_answer,
            "answer_delta": public_answer - local_answer,
            "local_route_accuracy": local_route,
            "public_route_accuracy": public_route,
            "route_delta": public_route - local_route,
            "local_evidence_hit_at_k": local_evidence,
            "public_evidence_hit_at_k": public_evidence,
            "evidence_delta": public_evidence - local_evidence,
        }
    return rows


def _diagnosis(
    local_test: dict[str, object],
    public_test: dict[str, object],
    family_delta: dict[str, dict[str, float]],
) -> list[str]:
    rows = [
        f"Overall answer accuracy delta public-minus-local is {public_test['answer_accuracy'] - local_test['answer_accuracy']:.3f}.",
        f"Overall route accuracy delta public-minus-local is {public_test['route_accuracy'] - local_test['route_accuracy']:.3f}.",
    ]
    weakest = min(family_delta, key=lambda family: family_delta[family]["answer_delta"]) if family_delta else "none"
    if weakest != "none":
        row = family_delta[weakest]
        rows.append(
            f"Most degraded family is {weakest}: answer delta {row['answer_delta']:.3f}, "
            f"route delta {row['route_delta']:.3f}, evidence delta {row['evidence_delta']:.3f}."
        )
        if row["route_delta"] < row["evidence_delta"]:
            rows.append("Routing appears to explain more degradation than retrieval for the weakest family.")
        else:
            rows.append("Retrieval/evidence grounding appears to explain more degradation than routing for the weakest family.")
    return rows


def _markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Public Raw Vs Local Normalized Grounding",
        "",
        f"Local normalized source: `{payload['local_normalized_source']}`.",
        f"Public raw source: `{payload['public_raw_source']}`.",
        "",
        "## Overall Delta",
        "",
        f"- Local normalized test answer accuracy: {payload['local_normalized_test_answer_accuracy']:.3f}.",
        f"- Public raw test answer accuracy: {payload['public_raw_test_answer_accuracy']:.3f}.",
        f"- Public-minus-local answer delta: {payload['overall_answer_accuracy_delta']:.3f}.",
        f"- Local normalized test route accuracy: {payload['local_normalized_test_route_accuracy']:.3f}.",
        f"- Public raw test route accuracy: {payload['public_raw_test_route_accuracy']:.3f}.",
        f"- Public-minus-local route delta: {payload['overall_route_accuracy_delta']:.3f}.",
        "",
        "## Per-Family Delta",
        "",
    ]
    for family, row in payload["per_family_delta"].items():
        lines.append(
            f"- {family}: answer delta {row['answer_delta']:.3f}, route delta {row['route_delta']:.3f}, "
            f"evidence delta {row['evidence_delta']:.3f}."
        )
    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
            *[f"- {item}" for item in payload["diagnosis"]],
            "",
            "## Threats To Validity",
            "",
            *[f"- {item}" for item in payload["threats_to_validity"]],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{JSON_PATH}`",
            f"- Markdown: `{MARKDOWN_PATH}`",
            f"- Plot: `{PLOT_PATH}`",
            "",
        ]
    )
    return "\n".join(lines)


def _matplotlib_pyplot():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/prism_matplotlib_cache")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_family_delta(payload: dict[str, object], path: Path) -> None:
    plt = _matplotlib_pyplot()
    families = sorted(payload["per_family_delta"])
    values = [payload["per_family_delta"][family]["answer_delta"] for family in families]
    _, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(families, values, color=["#c53030" if value < 0 else "#2f855a" for value in values])
    ax.axhline(0.0, color="#2d3748", linewidth=1)
    ax.set_title("Public raw minus local normalized answer accuracy")
    ax.set_ylabel("Answer accuracy delta")
    ax.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare local-normalized and public-raw grounding results.")
    parser.parse_args()
    payload = compare_grounding()
    print(
        "public_vs_local_grounding "
        f"answer_delta={payload['overall_answer_accuracy_delta']:.3f} "
        f"route_delta={payload['overall_route_accuracy_delta']:.3f} "
        f"json={JSON_PATH} markdown={MARKDOWN_PATH}"
    )
    for item in payload["diagnosis"]:
        print(item)


if __name__ == "__main__":
    main()
