# PRISM Team Plan Overview

## Current Stable State

PRISM is already safe to demo from Ritik's production path:

- Curated 80-query benchmark is restored to `80/80` end-to-end.
- External mini-benchmark is at `32/32`.
- Dense retrieval uses `sentence-transformers/all-MiniLM-L6-v2` with FAISS and a documented robustness rerank.
- BM25, Dense, KG, Hybrid, answer synthesis, reasoning traces, demo app, and analysis/report artifacts are present.
- Failure-analysis artifacts document the Dense tradeoff honestly, including the unsupported strict BM25-over-Dense lexical claim.

The project can still be demoed by Ritik alone if every optional teammate track remains unfinished.

## Why Work Is Split This Way

The split protects the demo by keeping all production routing, app behavior, final gold labels, final narrative, and final merge decisions under Ritik's control. The other three tracks improve evidence, analysis, and optional extensions without becoming blockers.

Each teammate should work in additive files or clearly scoped modules. Risky changes must be behind a config flag, a separate CLI, or a separate output artifact first.

## Ownership Summary

| Person | Track | Main Goal | Risk Level |
| --- | --- | --- | --- |
| Ritik | Critical path and final integration | Keep the demo, router, answer flow, report, and slides coherent | Required |
| Omkar | Dense, semantic, external generalization | Add optional Dense comparisons and semantic diagnostics | Optional |
| Vaishnavi | KG, deductive, structured reasoning | Add optional KG comparison and harder deductive cases | Optional |
| Moin | Claims, failure analysis, research evidence | Add report-support artifacts, rubrics, and limitations analysis | Optional |

## Timeline For The Next 10-12 Days

This is a phase plan, not a hard calendar. If time is short, protect Phase 4 and the demo.

## Phase 1: Setup And Task Kickoff

Goal: each teammate gets the repo running and chooses the first small deliverable.

- Everyone pulls/receives the latest repo state.
- Everyone runs the baseline commands listed in their individual plan.
- Everyone creates an additive work branch or clearly separate file set.
- Nobody edits Ritik-owned production files without approval.

Exit condition: each teammate can run tests or at least the relevant verifier for their track.

## Phase 2: Individual Implementation

Goal: each teammate creates one useful optional artifact or module.

- Omkar runs Dense comparisons or semantic diagnostics.
- Vaishnavi adds KG comparison artifacts or harder optional deductive cases.
- Moin expands claim/failure-analysis artifacts and limitations support.
- Ritik keeps the demo/report path stable and rejects risky changes early.

Exit condition: each track has a small, reviewable result with commands and outputs.

## Phase 3: Artifact Generation And Comparison

Goal: convert optional work into report-ready evidence.

- Generate JSON, CSV, Markdown, or PNG artifacts.
- Keep all new outputs in predictable paths.
- Compare optional results against the current stable baseline.
- Do not silently overwrite final gold labels or demo behavior.

Exit condition: useful artifacts can be cited in appendix/slides even if code is not merged into production.

## Phase 4: Merge, Final Demo, And Report Polish

Goal: freeze the demo path and finish the final story.

- Ritik reviews all contributions.
- Only low-risk additive changes are accepted.
- Run full acceptance commands.
- Freeze demo queries and final slide flow.
- Do at least one full dry run from a clean shell.

Exit condition: PRISM can be presented reliably without relying on unfinished optional tracks.

## Minimum Shared Commands

Use the project virtual environment. If `.venv/bin/python3` exists, use it.

```bash
.venv/bin/python3 -m pip install -e .
.venv/bin/python3 -m pytest -q
.venv/bin/python3 -m prism.ingest.build_corpus
.venv/bin/python3 -m prism.ingest.build_kg
.venv/bin/python3 -m prism.eval.verify_end_to_end
```

## Safety Principle

If a teammate's work does not finish, PRISM remains demo-ready. Optional tracks should create evidence that strengthens the report, not dependencies that can break the demo.
