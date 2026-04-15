# Ritik Plan: Production Demo And Final Integration

## Objective

Own the critical path and keep PRISM demo-safe. Ritik controls production integration, routing behavior, final answer flow, final benchmark labels, final report narrative, slide flow, and merge decisions.

## Files And Modules Ritik May Edit

- `prism/app/*`
- `prism/demo/*`
- `prism/answering/*`
- `prism/ras/*`
- `prism/eval/*` when final gold labels or final benchmark behavior are involved
- `configs/*`
- `README.md`
- final report, slide, and submission documents
- final generated demo/report artifacts under `data/eval/*`

## Files And Modules Ritik Controls Exclusively

Only Ritik should directly control these without prior agreement:

- `prism/app/*`
- `prism/demo/*`
- `prism/answering/*`
- `prism/ras/*`
- final benchmark gold labels
- final report narrative
- final presentation flow

## Files Ritik Should Review Before Accepting Changes

- Any change that affects routing decisions.
- Any change that affects demo output.
- Any change that modifies benchmark gold answers or evidence ids.
- Any change that weakens an evaluation threshold.
- Any change that changes existing CLI output semantics.

## Deliverables

- A stable final demo path.
- Final route-family slide flow: BM25, Dense, KG, Hybrid.
- Final report narrative explaining structural mismatch and RAS routing.
- Final dry-run checklist.
- Accepted/rejected contribution notes for Omkar, Vaishnavi, and Moin.
- Final artifact refresh after all accepted contributions.

## Starting Checklist

- Confirm repo runs from the virtual environment.
- Run `.venv/bin/python3 -m pytest -q`.
- Run `.venv/bin/python3 -m prism.eval.verify_end_to_end`.
- Run `.venv/bin/python3 -m prism.external_benchmarks.verify_generalization`.
- Run `.venv/bin/python3 -m prism.analysis.report_artifacts`.
- Open the demo and verify the four canonical queries:
  - `RFC-7231`
  - `What feels like climate anxiety?`
  - `Can a mammal fly?`
  - `What bridge connects bat and vertebrate?`

## Step-By-Step Work Plan

1. Freeze the production demo query set.
2. Review the current report artifacts and decide which plots/tables are final.
3. Review teammate changes only after they provide files changed, commands run, test results, artifacts, summary, and limitations.
4. Accept only additive or clearly beneficial changes.
5. Reject or defer changes that modify production routing, final gold labels, or demo behavior without a strong reason.
6. Regenerate final artifacts after any accepted merge.
7. Run a full demo dry run from a fresh terminal.
8. Prepare final slides around the existing stable story, not around unfinished optional work.

## Definition Of Done

- Demo runs locally without internet after artifacts/models are available.
- End-to-end benchmark remains passing.
- External mini-benchmark remains reported honestly.
- Final report includes both strengths and limitations.
- Slide flow can be presented without relying on unfinished teammate work.
- All accepted teammate contributions are documented and reproducible.

## Failure-Safe Note

If no teammate contribution finishes, Ritik still presents the current PRISM system. The core demo, benchmarks, analysis artifacts, and failure-analysis layer are already sufficient for a defensible presentation.
