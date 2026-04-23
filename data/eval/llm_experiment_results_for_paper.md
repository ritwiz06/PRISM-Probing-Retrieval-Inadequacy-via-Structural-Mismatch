# LLM-Assisted PRISM Experiment Results For Paper

## What The LLM Was Allowed To See
The LLM router prompt includes the user query, compact backend definitions, parsed query features, computed RAS scores, and optional evidence hints. It is not allowed to answer the query during routing.

## What Was Evaluated
The experiment is analysis-only: local LLM routing and evidence-grounded answer/trace refinement are compared against computed RAS, calibrated rescue, classifier routing, and fixed backends.

## Runtime Result
No local LLM endpoint was available during this run, so the repo generated the evaluation harness, baseline comparisons, setup guidance, plots, and partial human-alignment artifacts without fabricating LLM metrics.

## Tradeoffs
- Computed RAS remains more inspectable and deterministic.
- LLM routing may be useful on ambiguous prompts, but it must be judged against evidence support and human preference rather than treated as ground truth.
- Evidence-grounded refinement can improve readability only if it preserves evidence ids and does not introduce unsupported facts.
