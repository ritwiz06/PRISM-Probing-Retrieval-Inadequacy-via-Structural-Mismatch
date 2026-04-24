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

$$
p_r(x)=1+\Delta_r^{lex}(x)+\Delta_r^{sem}(x)+\Delta_r^{ded}(x)+\Delta_r^{rel}(x)
$$

$$
\hat r=\arg\min_{r\in R}p_r(x)
$$

Key penalty terms: $\Delta_{bm25}^{lex}=-0.6$, $\Delta_{dense}^{lex}=+0.2$, $\Delta_{dense}^{sem}=-0.5$, $\Delta_{kg}^{ded}=-0.6$, $\Delta_{hybrid}^{rel}=-0.7$, and $\Delta_{kg}^{rel}=-0.2$.

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

$$
s_r(x)=b_r+\sum_j w_{rj}f_j(x)
$$

$$
\hat r_{v3}=\arg\max_{r\in R}s_r(x)
$$

Each route receives a linear score. Explanations report active features and their weighted contribution for each route.

## RAS_V4

Status: `analysis-only`.

Route feature count: `31`.

Evidence feature count: `23`.

Equation:

$$
z_r(x)=b+\sum_j\alpha_j q_j(x,r)+\sum_k\beta_k e_k(E_r(x),x)
$$

$$
\hat r_{v4}=\arg\max_{r\in R}z_r(x)
$$

RAS_V4 is the cleanest research framing because it separates route adequacy from evidence adequacy. Recorded results still keep it analysis-only because calibrated rescue remains stronger on adversarial answer accuracy.

## Calibrated Rescue

Calibrated rescue is not a RAS version. It is a research overlay that shows route choice and evidence use are complementary.
