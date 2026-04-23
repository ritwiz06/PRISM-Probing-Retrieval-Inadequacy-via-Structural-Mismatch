# RAS V3 Case Studies

Case selection: adversarial-test examples where RAS_V3 changed computed RAS, falling back to representative RAS_V3 cases.

## adv_bm25_test_05

Query: HTML aria-labelledby looks like accessibility semantics; what does that exact attribute identify?
Gold route: `bm25`. RAS_V3 route: `dense`.
Route correct: `False`. Answer correct: `True`.
Rationale: RAS_V3 selected dense with highest linear adequacy score 1.600. Largest active contributions: token_count_log=+0.528, keyword_route_dense=+0.434, source_adversarial=+0.351, query_length_log=+0.313. Runner-up was bm25 at 0.003.

Top contributions:
- `token_count_log`: +0.528
- `keyword_route_dense`: +0.434
- `source_adversarial`: +0.351
- `query_length_log`: +0.313
- `intercept`: -0.243
- `computed_route_bm25`: +0.143

## adv_dense_test_01

Query: Which learning setup lets an agent improve from rewards, although the word policy appears like a legal section?
Gold route: `dense`. RAS_V3 route: `dense`.
Route correct: `True`. Answer correct: `True`.
Rationale: RAS_V3 selected dense with highest linear adequacy score 1.158. Largest active contributions: token_count_log=+0.607, source_adversarial=+0.351, query_length_log=+0.323, negation_or_contrast=-0.175. Runner-up was bm25 at 0.159.

Top contributions:
- `token_count_log`: +0.607
- `source_adversarial`: +0.351
- `query_length_log`: +0.323
- `intercept`: -0.243
- `negation_or_contrast`: -0.175
- `computed_route_bm25`: +0.143

## adv_dense_test_02

Query: What model keeps materials in use rather than waste, despite the exact phrase jsonb_set in the distractor?
Gold route: `dense`. RAS_V3 route: `dense`.
Route correct: `True`. Answer correct: `True`.
Rationale: RAS_V3 selected dense with highest linear adequacy score 2.356. Largest active contributions: semantic_abstraction=+1.432, token_count_log=+0.595, source_adversarial=+0.351, query_length_log=+0.319. Runner-up was bm25 at 0.527.

Top contributions:
- `semantic_abstraction`: +1.432
- `token_count_log`: +0.595
- `source_adversarial`: +0.351
- `query_length_log`: +0.319
- `intercept`: -0.243
- `public_document_noise`: -0.220

## adv_dense_test_04

Query: What view of word meaning uses nearby contexts even though the query says lexical identifier?
Gold route: `dense`. RAS_V3 route: `dense`.
Route correct: `True`. Answer correct: `True`.
Rationale: RAS_V3 selected dense with highest linear adequacy score 2.889. Largest active contributions: semantic_abstraction=+1.432, token_count_log=+0.571, keyword_route_dense=+0.434, source_adversarial=+0.351. Runner-up was bm25 at 0.266.

Top contributions:
- `semantic_abstraction`: +1.432
- `token_count_log`: +0.571
- `keyword_route_dense`: +0.434
- `source_adversarial`: +0.351
- `query_length_log`: +0.311
- `intercept`: -0.243
