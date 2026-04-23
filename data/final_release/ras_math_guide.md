# RAS Math Guide

## Notation

- `x`: query text.
- `r`: candidate route in `{bm25, dense, kg, hybrid}`.
- `f(x)`: query feature vector.
- `E_r(x)`: top-k evidence retrieved by backend `r`.
- `margin`: gap between winner and runner-up. For `computed_ras`, lower score is better; for RAS_V3/RAS_V4, higher score is better.

## computed_ras

Status: `production`.

Score convention: `lower is better`.

Formula:

```text
Initialize p_r=1.0 for r in {bm25,dense,kg,hybrid}. If lexical: p_bm25 -= 0.6 and p_dense += 0.2. If semantic: p_dense -= 0.5. If deductive: p_kg -= 0.6. If relational: p_hybrid -= 0.7 and p_kg -= 0.2. Select argmin_r p_r.
```

This is a heuristic penalty table, not a learned model. It is production because it is deterministic, stable, and easy to audit.

## computed_ras_v2

Status: `analysis-only`.

RAS_V2 starts from computed RAS, then applies these narrow route correction rules:

- Start with computed_ras selected backend.
- If relational marker appears, select hybrid.
- Else if deductive marker appears and no strong identifier appears, select kg.
- Else if identifier-heavy plus semantic ambiguity and no strong identifier, select dense.
- Else if identifier-heavy plus strong identifier, select bm25.
- Else if formal source-pack prior plus identifier-heavy, select bm25.
- Else if margin < 0.15 and semantic-only, select dense.

It is useful for explaining hard-case route-boundary ideas, but it is not production.

## RAS_V3

Status: `analysis-only`.

Feature count: `31`.

Equation:

```text
For each route r, compute s_r = b_r + sum_j w_{r,j} f_j(x). The implementation uses multinomial logistic regression weights but routes by max linear score. Select argmax_r s_r.
```

Each route receives a linear score. Explanations report active features and their weighted contribution for each route.

## RAS_V4

Status: `analysis-only`.

Route feature count: `31`.

Evidence feature count: `23`.

Equation:

```text
For each candidate backend r, compute z_r = b + sum_j alpha_j route_j(x) + sum_k beta_k evidence_k(E_r(x), x). Select argmax_r z_r. The score decomposes into route contribution, evidence contribution, and intercept.
```

RAS_V4 is the cleanest research framing because it separates route adequacy from evidence adequacy. Recorded results still keep it analysis-only because calibrated rescue remains stronger on adversarial answer accuracy.

## Calibrated Rescue

Calibrated rescue is not a RAS version. It is a research overlay that shows route choice and evidence use are complementary.
