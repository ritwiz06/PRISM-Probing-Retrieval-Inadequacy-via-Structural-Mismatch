from __future__ import annotations

import argparse
from pathlib import Path

from prism.analysis.evaluation import evaluate_systems
from prism.utils import write_json

ABLATION_SYSTEMS = ["computed_ras", "always_hybrid", "hybrid_no_kg", "hybrid_no_bm25", "hybrid_no_dense"]


def run_ablations() -> dict[str, object]:
    evaluation = evaluate_systems(system_names=ABLATION_SYSTEMS)
    systems = evaluation["systems"]
    baseline = systems["always_hybrid"]["per_slice"]["relational"]["evidence_hit_at_k"]
    impacts = []
    for name in ("hybrid_no_kg", "hybrid_no_bm25", "hybrid_no_dense"):
        relational = systems[name]["per_slice"]["relational"]
        impacts.append(
            {
                "ablation": name,
                "relational_evidence_hit_at_k": relational["evidence_hit_at_k"],
                "relational_answer_accuracy": relational["answer_accuracy"],
                "delta_vs_full_hybrid_evidence_hit_at_k": relational["evidence_hit_at_k"] - baseline,
            }
        )
    payload = {
        "systems": systems,
        "ablation_impacts": impacts,
        "summary": "Hybrid ablations disable one contributing backend at a time while preserving the same RRF retriever interface.",
    }
    output_path = Path("data/eval/ablation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PRISM retrieval/router ablations.")
    parser.parse_args()
    payload = run_ablations()
    print(f"ablations={len(payload['ablation_impacts'])} output=data/eval/ablation_results.json")
    for row in payload["ablation_impacts"]:
        print(
            f"{row['ablation']}: relational_hit@k={row['relational_evidence_hit_at_k']:.3f} "
            f"delta_vs_full={row['delta_vs_full_hybrid_evidence_hit_at_k']:.3f}"
        )


if __name__ == "__main__":
    main()
