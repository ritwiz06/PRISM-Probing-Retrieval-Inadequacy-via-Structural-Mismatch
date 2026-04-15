# Vaishnavi Plan: KG, Deductive, And Structured Reasoning Extensions

## Objective

Own optional KG and deductive reasoning extensions. The goal is to strengthen the structured-reasoning story while preserving the curated KG path as the default, demo-safe path.

## Main Areas To Work In

- `prism/ingest/build_kg.py`
- `prism/retrievers/kg_retriever.py`
- KG-related evaluation files under `prism/eval/*`
- KG-related analysis files under `prism/analysis/*`
- new KG comparison artifacts under `data/eval/*`
- KG-specific tests

## Files And Modules To Avoid

Do not edit without Ritik's approval:

- `prism/app/*`
- `prism/demo/*`
- `prism/answering/*`
- `prism/ras/*`
- final benchmark gold labels
- production curated KG default behavior
- final report narrative and presentation flow

## Deliverables

Choose one or more, ordered by priority:

1. Curated-vs-extracted KG comparison artifact.
2. Optional extracted-KG mode that is disabled by default.
3. Harder deductive query appendix, kept separate from the final curated deductive slice.
4. KG error-analysis report for universal vs existential questions.
5. KG coverage summary with triple counts, relation types, and known gaps.

## Starting Checklist

- Run `.venv/bin/python3 -m pip install -e .`.
- Run `.venv/bin/python3 -m prism.ingest.build_kg`.
- Run `.venv/bin/python3 -m prism.eval.verify_kg`.
- Run `.venv/bin/python3 -m prism.eval.verify_end_to_end`.
- Read:
  - `prism/ingest/build_kg.py`
  - `prism/retrievers/kg_retriever.py`
  - `prism/eval/deductive_slice.py`
  - `data/eval/kg_verification.json`

## Step-By-Step Work Plan

1. Inspect the current curated KG triples and query modes.
2. Pick one optional KG extension and keep it separate from the default path.
3. If adding extracted triples, write them to a new optional artifact or require an explicit flag.
4. Preserve the current curated KG build as the default behavior.
5. Add a comparison CLI or report artifact if possible.
6. Add tests for output shape or optional-mode loading.
7. Run KG verification and end-to-end verification before handing off.

## Definition Of Done

- Curated KG path remains default and passes verification.
- No final gold labels are changed silently.
- Optional extracted or harder KG work is clearly labeled.
- New artifacts describe whether evidence supports, refutes, or is insufficient.
- Universal claims still show support/counterexample handling where relevant.

## Failure-Safe Note

If this track is unfinished, PRISM keeps the existing curated KG backend. Ritik can still show deductive reasoning and closed-world demo assumptions with the current verified KG.

## Handoff Checklist

Submit:

- Files changed.
- Commands run.
- Test results.
- Artifact paths.
- One-paragraph summary.
- Known limitations.
