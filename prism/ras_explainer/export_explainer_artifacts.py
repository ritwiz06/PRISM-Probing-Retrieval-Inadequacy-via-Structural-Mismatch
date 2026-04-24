from __future__ import annotations

import argparse
import json
from pathlib import Path

from prism.ras_explainer.math_docs import ras_math_payload
from prism.ras_explainer.sensitivity import build_sensitivity_artifacts
from prism.ras_explainer.version_compare import build_version_comparison, explain_query
from prism.utils import write_json

FINAL_RELEASE_DIR = Path("data/final_release")
EVAL_DIR = Path("data/eval")


def export_explainer_artifacts(
    *,
    release_dir: str | Path = FINAL_RELEASE_DIR,
    eval_dir: str | Path = EVAL_DIR,
    include_sensitivity: bool = True,
) -> dict[str, object]:
    release = Path(release_dir)
    eval_target = Path(eval_dir)
    release.mkdir(parents=True, exist_ok=True)
    eval_target.mkdir(parents=True, exist_ok=True)
    math_payload = ras_math_payload()
    comparison = build_version_comparison()
    example = explain_query("Which concept feels like RFC-7231 but is about worry?", source_type="adversarial")
    summary = {
        "production_router": "computed_ras",
        "research_overlays": ["computed_ras_v2", "ras_v3", "ras_v4", "calibrated_rescue"],
        "math_payload": math_payload,
        "version_comparison": comparison,
        "example_query_explanation": example,
        "sensitivity": build_sensitivity_artifacts(eval_target) if include_sensitivity else {"status": "not_requested"},
        "release_docs": {
            "ras_overview": str(release / "ras_overview.md"),
            "ras_math_guide": str(release / "ras_math_guide.md"),
            "ras_version_comparison": str(release / "ras_version_comparison.md"),
            "ras_visual_explanation": str(release / "ras_visual_explanation.md"),
            "ras_quick_reference": str(release / "ras_quick_reference.md"),
        },
    }
    _write_release_docs(release, math_payload, comparison)
    write_json(eval_target / "ras_explainer_summary.json", summary)
    print(
        "ras_explainer_artifacts "
        f"release_dir={release} eval_dir={eval_target} production_router=computed_ras "
        f"sensitivity={summary['sensitivity'].get('item_count', 'skipped') if isinstance(summary['sensitivity'], dict) else 'unknown'}"
    )
    return summary


def write_release_docs(release_dir: str | Path = FINAL_RELEASE_DIR) -> dict[str, str]:
    release = Path(release_dir)
    release.mkdir(parents=True, exist_ok=True)
    math_payload = ras_math_payload()
    comparison = build_version_comparison()
    _write_release_docs(release, math_payload, comparison)
    return {
        "ras_overview": str(release / "ras_overview.md"),
        "ras_math_guide": str(release / "ras_math_guide.md"),
        "ras_version_comparison": str(release / "ras_version_comparison.md"),
        "ras_visual_explanation": str(release / "ras_visual_explanation.md"),
        "ras_quick_reference": str(release / "ras_quick_reference.md"),
    }


def _write_release_docs(release: Path, math_payload: dict[str, object], comparison: dict[str, object]) -> None:
    (release / "ras_overview.md").write_text(_ras_overview(), encoding="utf-8")
    (release / "ras_math_guide.md").write_text(_ras_math_guide(math_payload), encoding="utf-8")
    (release / "ras_version_comparison.md").write_text(_ras_version_comparison(comparison), encoding="utf-8")
    (release / "ras_visual_explanation.md").write_text(_ras_visual_explanation(), encoding="utf-8")
    (release / "ras_quick_reference.md").write_text(_ras_quick_reference(comparison), encoding="utf-8")


def _ras_overview() -> str:
    return """# RAS Overview

RAS means Representation Adequacy Score. In PRISM, RAS estimates which retrieval representation is structurally adequate for a query before the answer is generated.

The core thesis is simple: retrieval fails when the representation does not match the question. Exact identifiers are better served by BM25. Conceptual paraphrases are better served by Dense retrieval. Deductive membership or property questions need KG-style structure. Relational bridge questions often need Hybrid retrieval.

Production PRISM uses `computed_ras`, a deterministic penalty-table router. Later variants are research layers:

- `computed_ras_v2` adds narrow hard-case correction rules.
- `ras_v3` learns an interpretable route-adequacy score from features.
- `ras_v4` adds evidence-adequacy diagnostics to route adequacy.
- `calibrated_rescue` is an overlay showing that top-k evidence rescue is complementary to route choice.

The release decision remains explicit: production router = `computed_ras`. Learned and rescue layers are analysis/demo overlays.
"""


def _ras_math_guide(payload: dict[str, object]) -> str:
    computed = payload["computed_ras"]
    v2 = payload["computed_ras_v2"]
    v3 = payload["ras_v3"]
    v4 = payload["ras_v4"]
    return f"""# RAS Math Guide

## Notation

- `x`: query text.
- `r`: candidate route in `{{bm25, dense, kg, hybrid}}`.
- `f(x)`: query feature vector.
- `E_r(x)`: top-k evidence retrieved by backend `r`.
- `margin`: gap between winner and runner-up. For `computed_ras`, lower score is better; for RAS_V3/RAS_V4, higher score is better.

## computed_ras

Status: `{computed['status']}`.

Score convention: `{computed['score_convention']}`.

Formula:

$$
p_r(x)=1+\\Delta_r^{{lex}}(x)+\\Delta_r^{{sem}}(x)+\\Delta_r^{{ded}}(x)+\\Delta_r^{{rel}}(x)
$$

$$
\\hat r=\\arg\\min_{{r\\in R}}p_r(x)
$$

Key penalty terms: $\\Delta_{{bm25}}^{{lex}}=-0.6$, $\\Delta_{{dense}}^{{lex}}=+0.2$, $\\Delta_{{dense}}^{{sem}}=-0.5$, $\\Delta_{{kg}}^{{ded}}=-0.6$, $\\Delta_{{hybrid}}^{{rel}}=-0.7$, and $\\Delta_{{kg}}^{{rel}}=-0.2$.

This is a heuristic penalty table, not a learned model. It is production because it is deterministic, stable, and easy to audit.

## computed_ras_v2

Status: `{v2['status']}`.

RAS_V2 starts from computed RAS, then applies these narrow route correction rules:

{_bullets(v2['rule_recipe'])}

It is useful for explaining hard-case route-boundary ideas, but it is not production.

## RAS_V3

Status: `{v3['status']}`.

Feature count: `{v3['feature_count']}`.

Equation:

$$
s_r(x)=b_r+\\sum_j w_{{rj}}f_j(x)
$$

$$
\\hat r_{{v3}}=\\arg\\max_{{r\\in R}}s_r(x)
$$

Each route receives a linear score. Explanations report active features and their weighted contribution for each route.

## RAS_V4

Status: `{v4['status']}`.

Route feature count: `{v4['route_feature_count']}`.

Evidence feature count: `{v4['evidence_feature_count']}`.

Equation:

$$
z_r(x)=b+\\sum_j\\alpha_j q_j(x,r)+\\sum_k\\beta_k e_k(E_r(x),x)
$$

$$
\\hat r_{{v4}}=\\arg\\max_{{r\\in R}}z_r(x)
$$

RAS_V4 is the cleanest research framing because it separates route adequacy from evidence adequacy. Recorded results still keep it analysis-only because calibrated rescue remains stronger on adversarial answer accuracy.

## Calibrated Rescue

Calibrated rescue is not a RAS version. It is a research overlay that shows route choice and evidence use are complementary.
"""


def _ras_version_comparison(comparison: dict[str, object]) -> str:
    rows = comparison["versions"]
    lines = [
        "# RAS Version Comparison",
        "",
        "| Version | Status | Model type | Selection rule | Uses evidence | Learned | Strength | Weakness |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {name} | {status} | {model_type} | {selection_rule} | {uses_evidence} | {learned} | {strength} | {weakness} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Empirical Snapshot",
            "",
            "```json",
            json.dumps(comparison.get("empirical_snapshot", {}), indent=2),
            "```",
            "",
            f"Promotion decision: `{comparison['promotion_decision']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _ras_visual_explanation() -> str:
    return """# RAS Visual Explanation

This sequence gives a compact visual story for slides, posters, and the Streamlit `RAS Explainer` page.

## Visual Story

1. Query arrives.
2. PRISM extracts route-relevant features: identifier-heavy, semantic abstraction, deductive cue, relational bridge cue, source context, and ambiguity signals.
3. Candidate routes receive scores.
4. The selected route retrieves evidence.
5. The answerer produces an evidence-cited answer and trace.
6. If margins are low or RAS variants disagree, PRISM surfaces an advisory ambiguity warning.

## How To Explain The Versions

- `computed_ras`: simple penalty table. Lower score wins.
- `computed_ras_v2`: computed RAS plus narrow rule corrections.
- `ras_v3`: learned but interpretable route-only score. Higher score wins.
- `ras_v4`: learned but interpretable joint route/evidence score. Higher score wins.
- `calibrated_rescue`: post-route rescue overlay, not the production router.

## Demo Guidance

Show route scores first, then evidence, then answer. This keeps PRISM's core distinction visible: route adequacy chooses the representation, evidence adequacy determines whether that route actually supports an answer.
"""


def _ras_quick_reference(comparison: dict[str, object]) -> str:
    return f"""# RAS Quick Reference

Production router: `computed_ras`.

Research overlays: `computed_ras_v2`, `ras_v3`, `ras_v4`, `calibrated_rescue`, optional LLM.

## What To Say In A Demo

- RAS estimates which representation is adequate for the query.
- `computed_ras` is the production router because it is deterministic and stable.
- RAS_V3 formalizes route adequacy with interpretable learned weights.
- RAS_V4 adds evidence adequacy, making the research story stronger.
- Calibrated rescue shows hard cases often need better use of top-k evidence, not only better route choice.

## What To Say In A Paper

PRISM's contribution is representation-aware routing. Route-only adequacy helps but is incomplete on adversarial hard cases. Joint route-and-evidence adequacy is the stronger research framing, while production remains conservative.

## Promotion Decision

{comparison['promotion_decision']}
"""


def _bullets(items: object) -> str:
    if not isinstance(items, list):
        return ""
    return "\n".join(f"- {item}" for item in items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export RAS explainer docs and sensitivity artifacts.")
    parser.add_argument("--release-dir", default=str(FINAL_RELEASE_DIR))
    parser.add_argument("--eval-dir", default=str(EVAL_DIR))
    parser.add_argument("--skip-sensitivity", action="store_true")
    args = parser.parse_args()
    export_explainer_artifacts(
        release_dir=args.release_dir,
        eval_dir=args.eval_dir,
        include_sensitivity=not args.skip_sensitivity,
    )


if __name__ == "__main__":
    main()
