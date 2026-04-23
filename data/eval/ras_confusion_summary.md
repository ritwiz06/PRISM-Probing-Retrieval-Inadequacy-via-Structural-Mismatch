# RAS Confusion and Ambiguity Summary

This artifact is analysis-only. It does not change the production router.

Total adversarial items: `48`.
Version disagreement count: `5`.
Low computed-RAS margin count: `7`.
Advisory ambiguity flag count: `11`.

## Computed RAS Confusion

- `bm25->bm25`: 10
- `bm25->kg`: 2
- `dense->bm25`: 10
- `dense->dense`: 2
- `hybrid->hybrid`: 12
- `kg->bm25`: 1
- `kg->kg`: 11

## Feature Ablation Summary

- `lexical`: 6/24 ablations changed the selected route
- `semantic`: 2/10 ablations changed the selected route
- `deductive`: 13/14 ablations changed the selected route
- `relational`: 12/12 ablations changed the selected route

## Interpretation

The ambiguity flag is advisory only. It indicates either a small production RAS margin or disagreement between analysis variants.
It should be used for explanation, caution, and demo interpretation, not automatic production override.
