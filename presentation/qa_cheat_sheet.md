# PRISM Q&A Cheat Sheet

## What is the central claim?

PRISM claims that many retrieval failures are structural mismatch failures. The system should choose the retrieval representation that matches the query structure.

## What is KRR about this project?

The KRR component is representation adequacy. PRISM reasons over query type, representation suitability, evidence provenance, and trace support before producing an answer.

## Why not just use Dense retrieval?

Dense retrieval is useful for semantic paraphrase, but it can be weak for exact identifiers, formal codes, deductive class/property questions, and graph-like bridge cases.

## What is the production router?

The production router is `computed_ras`.

## Did RAS_V3 or RAS_V4 replace computed_ras?

No. They are analysis-only research variants. They improve interpretability and formalization, but they were not promoted under the release guardrails.

## Why does calibrated rescue matter?

On adversarial test cases, calibrated rescue reaches 0.958 answer accuracy compared with computed_ras at 0.917. This shows that evidence adequacy and top-k rescue are complementary to route adequacy.

## Is PRISM web-scale search?

No. It is bounded source-pack, local-folder, URL-list, and benchmark-corpus QA with provenance. It is not arbitrary web-scale search.

## What is the main limitation?

Hard route-boundary and adversarial ambiguity cases remain the main weakness.
