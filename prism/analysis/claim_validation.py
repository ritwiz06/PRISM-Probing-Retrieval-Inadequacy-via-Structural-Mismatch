from __future__ import annotations

import argparse
from pathlib import Path

from prism.analysis.evaluation import evaluate_systems
from prism.utils import write_json


def validate_claims() -> dict[str, object]:
    evaluation = evaluate_systems()
    systems = evaluation["systems"]
    claims = [
        _claim(
            "lexical_queries_favor_bm25_over_dense",
            systems["always_bm25"]["per_slice"]["lexical"]["evidence_hit_at_k"],
            systems["always_dense"]["per_slice"]["lexical"]["evidence_hit_at_k"],
            "Lexical queries favor BM25 over Dense on evidence hit@k.",
        ),
        _claim(
            "semantic_queries_favor_dense_over_bm25",
            systems["always_dense"]["per_slice"]["semantic"]["evidence_hit_at_k"],
            systems["always_bm25"]["per_slice"]["semantic"]["evidence_hit_at_k"],
            "Semantic queries favor Dense over BM25 on evidence hit@k.",
        ),
        _claim(
            "deductive_queries_favor_kg_over_dense_bm25",
            systems["always_kg"]["per_slice"]["deductive"]["evidence_hit_at_k"],
            max(
                systems["always_dense"]["per_slice"]["deductive"]["evidence_hit_at_k"],
                systems["always_bm25"]["per_slice"]["deductive"]["evidence_hit_at_k"],
            ),
            "Deductive queries favor KG over Dense and BM25 on evidence hit@k.",
        ),
        _claim(
            "relational_queries_favor_hybrid_over_single_backends",
            systems["always_hybrid"]["per_slice"]["relational"]["evidence_hit_at_k"],
            max(
                systems["always_dense"]["per_slice"]["relational"]["evidence_hit_at_k"],
                systems["always_bm25"]["per_slice"]["relational"]["evidence_hit_at_k"],
                systems["always_kg"]["per_slice"]["relational"]["evidence_hit_at_k"],
            ),
            "Relational queries favor Hybrid over single backends on evidence hit@k.",
        ),
        _claim(
            "computed_ras_beats_or_matches_fixed_backends_overall",
            systems["computed_ras"]["answer_accuracy"],
            max(
                systems["always_bm25"]["answer_accuracy"],
                systems["always_dense"]["answer_accuracy"],
                systems["always_kg"]["answer_accuracy"],
                systems["always_hybrid"]["answer_accuracy"],
            ),
            "Computed RAS routing beats or matches the strongest fixed-backend baseline overall on answer accuracy.",
            allow_tie=True,
        ),
    ]
    payload = {
        "claims": claims,
        "all_supported": all(row["supported"] for row in claims),
        "baseline_summary": {
            name: {
                "route_accuracy": row["route_accuracy"],
                "evidence_hit_at_k": row["evidence_hit_at_k"],
                "answer_accuracy": row["answer_accuracy"],
            }
            for name, row in systems.items()
        },
    }
    output_path = Path("data/eval/claim_validation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return payload


def _claim(name: str, primary: float, baseline: float, statement: str, allow_tie: bool = False) -> dict[str, object]:
    supported = primary >= baseline if allow_tie else primary > baseline
    return {
        "name": name,
        "statement": statement,
        "primary_metric": primary,
        "baseline_metric": baseline,
        "margin": primary - baseline,
        "supported": supported,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate PRISM thesis claims against the local benchmark.")
    parser.parse_args()
    payload = validate_claims()
    print(f"claim_validation_supported={payload['all_supported']} claims={len(payload['claims'])} output=data/eval/claim_validation.json")
    for row in payload["claims"]:
        status = "SUPPORTED" if row["supported"] else "NOT_SUPPORTED"
        print(f"{status}: {row['statement']} margin={row['margin']:.3f}")


if __name__ == "__main__":
    main()
