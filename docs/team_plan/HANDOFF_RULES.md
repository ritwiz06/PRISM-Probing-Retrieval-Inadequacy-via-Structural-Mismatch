# PRISM Handoff Rules

## Core Rule

No one merges directly into Ritik's production path. Ritik reviews and accepts or rejects every teammate contribution that could affect the demo, final routing behavior, final answer behavior, final benchmark labels, or final narrative.

## Required Handoff Package

Every teammate must submit:

- Files changed.
- Commands run.
- Test results.
- Artifact paths.
- One-paragraph summary.
- Known limitations.

If any command failed, include the exact failure and whether the failure blocks the demo.

## Additive-First Policy

All teammate work should be additive and optional by default.

Preferred contribution styles:

- New CLI or analysis module.
- New artifact under `data/eval/` or `data/submission/`.
- New config-flagged experiment.
- New Markdown/CSV/JSON summary.
- Tests that validate output shape.

Avoid:

- Replacing production defaults without approval.
- Silently changing final gold labels.
- Silently changing demo behavior.
- Weakening thresholds to make a result pass.
- Hiding unsupported claims.

## Protected Areas

Only Ritik should directly control these unless he explicitly approves a change:

- `prism/app/*`
- `prism/demo/*`
- `prism/answering/*`
- `prism/ras/*`
- final benchmark gold labels
- final report narrative
- final presentation flow

## Risky Change Rules

Any risky change must first be:

- behind a config flag,
- in a separate module,
- in a separate CLI,
- or in a clearly separate artifact path.

Examples of risky changes:

- Changing routing weights or RAS scoring.
- Changing benchmark gold labels.
- Changing answer synthesis templates.
- Changing default retriever behavior.
- Replacing KG/corpus build defaults.
- Rewriting demo UI flow.

## Verification Expectations

At minimum, run the relevant command for your track:

- Dense/semantic: `.venv/bin/python3 -m prism.eval.verify_semantic`
- External benchmark: `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`
- KG/deductive: `.venv/bin/python3 -m prism.eval.verify_kg`
- Hybrid/relational: `.venv/bin/python3 -m prism.eval.verify_hybrid`
- Analysis/report: `.venv/bin/python3 -m prism.analysis.report_artifacts`
- Full safety check: `.venv/bin/python3 -m prism.eval.verify_end_to_end`

Run `.venv/bin/python3 -m pytest -q` if your change affects Python code.

## If Work Is Incomplete

Incomplete work should be handed off as optional notes or a draft artifact, not merged into the production path. PRISM remains demo-ready without optional tracks.

## Final Merge Rule

Before final merge, Ritik should check:

- Does the demo still run?
- Does `verify_end_to_end` still pass?
- Are benchmark/gold-label changes explicit and justified?
- Are unsupported claims still reported honestly?
- Are new artifacts useful for the report or appendix?

If the answer to any of these is no, defer the contribution.
