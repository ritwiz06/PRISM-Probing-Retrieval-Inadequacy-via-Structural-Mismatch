# Q&A Cheat Sheet

## What is PRISM?
- A representation-aware retrieval router for BM25, Dense, KG, and Hybrid evidence.

## What is the production router?
- `computed_ras`.

## Why not promote RAS_V3 or RAS_V4?
- They improve the research framing and interpretability, but they do not beat calibrated rescue on adversarial answer accuracy.

## Why does calibrated rescue matter?
- It shows that route choice alone is not the full target; top-k evidence use still matters on hard cases.

## Is this web-scale QA?
- No. PRISM supports bounded benchmark corpora, source packs, local folders, and URL-list corpora.

## What is the strongest failure regime?
- Adversarial route-boundary cases, especially misleading exact terms and low-margin ambiguity.

## What did human evaluation add?
- It confirmed that evidence and traces are usually useful and faithful, while preserving ties, disagreements, and adjudication cases.
