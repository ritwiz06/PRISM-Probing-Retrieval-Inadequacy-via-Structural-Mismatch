# RAS V4 Case Studies

Case selection: adversarial-test examples where RAS_V4 changed computed RAS, falling back to representative cases.

## adv_bm25_test_01

Query: Authentication framework, but do not answer with semantics: RFC-7235 is the exact target.
Gold route: `bm25`. RAS_V4 route: `bm25`.
Rationale: RAS_V4 selected bm25 with combined adequacy score 3.284 (route=+1.600, evidence=+5.505, margin=5.620). Top contributions: evidence__candidate_matches_computed_ras=+4.300, intercept=-3.821, evidence__candidate_matches_keyword=+2.000, evidence__top1_score=+0.991, evidence__identifier_exact_match=-0.925.

Route contribution: `1.600`. Evidence contribution: `5.505`.

Top contributions:
- `evidence__candidate_matches_computed_ras`: +4.300
- `intercept`: -3.821
- `evidence__candidate_matches_keyword`: +2.000
- `evidence__top1_score`: +0.991
- `evidence__identifier_exact_match`: -0.925
- `evidence__source_diversity`: -0.828

## adv_bm25_test_02

Query: HIPAA 164.510 opportunity to agree or object, with 164.512 nearby in the page noise.
Gold route: `bm25`. RAS_V4 route: `bm25`.
Rationale: RAS_V4 selected bm25 with combined adequacy score 4.278 (route=+1.305, evidence=+6.794, margin=5.763). Top contributions: evidence__candidate_matches_computed_ras=+4.300, intercept=-3.821, evidence__candidate_matches_keyword=+2.000, evidence__top1_score=+0.992, evidence__source_diversity=-0.828.

Route contribution: `1.305`. Evidence contribution: `6.794`.

Top contributions:
- `evidence__candidate_matches_computed_ras`: +4.300
- `intercept`: -3.821
- `evidence__candidate_matches_keyword`: +2.000
- `evidence__top1_score`: +0.992
- `evidence__source_diversity`: -0.828
- `evidence__semantic_snippet_consistency`: +0.590

## adv_bm25_test_03

Query: numpy.linalg.norm describes geometry and magnitude, but the exact function is the answer source.
Gold route: `bm25`. RAS_V4 route: `bm25`.
Rationale: RAS_V4 selected bm25 with combined adequacy score 4.389 (route=+2.227, evidence=+5.983, margin=6.252). Top contributions: evidence__candidate_matches_computed_ras=+4.300, intercept=-3.821, evidence__candidate_matches_keyword=+2.000, evidence__top1_score=+0.979, evidence__identifier_exact_match=-0.925.

Route contribution: `2.227`. Evidence contribution: `5.983`.

Top contributions:
- `evidence__candidate_matches_computed_ras`: +4.300
- `intercept`: -3.821
- `evidence__candidate_matches_keyword`: +2.000
- `evidence__top1_score`: +0.979
- `evidence__identifier_exact_match`: -0.925
- `evidence__source_diversity`: -0.828

## adv_bm25_test_04

Query: PostgreSQL jsonb_insert, not jsonb_set, inserts what into a JSONB document?
Gold route: `bm25`. RAS_V4 route: `bm25`.
Rationale: RAS_V4 selected bm25 with combined adequacy score 3.991 (route=+1.639, evidence=+6.173, margin=5.701). Top contributions: evidence__candidate_matches_computed_ras=+4.300, intercept=-3.821, evidence__candidate_matches_keyword=+2.000, evidence__top1_score=+0.993, evidence__identifier_exact_match=-0.925.

Route contribution: `1.639`. Evidence contribution: `6.173`.

Top contributions:
- `evidence__candidate_matches_computed_ras`: +4.300
- `intercept`: -3.821
- `evidence__candidate_matches_keyword`: +2.000
- `evidence__top1_score`: +0.993
- `evidence__identifier_exact_match`: -0.925
- `evidence__source_diversity`: -0.828

## adv_bm25_test_05

Query: HTML aria-labelledby looks like accessibility semantics; what does that exact attribute identify?
Gold route: `bm25`. RAS_V4 route: `bm25`.
Rationale: RAS_V4 selected bm25 with combined adequacy score 1.799 (route=+1.022, evidence=+4.598, margin=1.706). Top contributions: evidence__candidate_matches_computed_ras=+4.300, intercept=-3.821, evidence__top1_score=+0.989, evidence__source_diversity=-0.828, route__lexical_exactness=+0.378.

Route contribution: `1.022`. Evidence contribution: `4.598`.

Top contributions:
- `evidence__candidate_matches_computed_ras`: +4.300
- `intercept`: -3.821
- `evidence__top1_score`: +0.989
- `evidence__source_diversity`: -0.828
- `route__lexical_exactness`: +0.378
- `route__source_adversarial`: +0.358
