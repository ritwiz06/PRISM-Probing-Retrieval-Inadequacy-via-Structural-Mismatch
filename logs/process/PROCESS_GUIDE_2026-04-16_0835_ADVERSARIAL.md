# PROCESS GUIDE - 2026-04-16 08:35 - Adversarial Hard-Case Evaluation

## Basic Summary

This task added a hard-case evaluation layer for PRISM. Earlier benchmarks showed PRISM working very well on curated, held-out, noisy, public raw, and public graph settings. The new adversarial layer asks a different question: where does PRISM fail when queries are intentionally ambiguous across BM25, Dense, KG, and Hybrid routes?

The production demo path did not change. Computed RAS remains the production router. The new adversarial package is an additive research/evaluation layer.

## What Was Implemented

The new package is `prism/adversarial/`.

- `query_templates.py` defines the allowed ambiguity tags and difficulty labels.
- `loaders.py` defines the normalized benchmark item schema and load/write helpers.
- `benchmark_builder.py` builds a separate 48-example hard benchmark.
- `verify_adversarial.py` evaluates computed RAS, router baselines, fixed-backend baselines, confidence, and targeted ablations.
- `failure_analysis.py` categorizes hard-case misses into interpretable buckets.

The benchmark artifact is:

- `data/processed/adversarial_benchmark.jsonl`

The main evaluation artifacts are:

- `data/eval/adversarial_eval.json`
- `data/eval/adversarial_eval.csv`
- `data/eval/adversarial_eval_summary.md`
- `data/eval/adversarial_confidence.json`
- `data/eval/adversarial_confidence_summary.md`
- `data/eval/adversarial_ablation_summary.md`
- `data/eval/adversarial_failure_analysis.json`
- `data/eval/adversarial_failure_analysis_summary.md`

Plots are:

- `data/eval/adversarial_baselines_by_tag.png`
- `data/eval/adversarial_confidence_error_rate.png`
- `data/eval/adversarial_top1_topk_gap.png`

## How The Hard Benchmark Is Built

The hard benchmark is intentionally separate from the existing curated, external, generalization v2, public raw, and public graph benchmarks.

It contains `48` examples:

- `24` dev examples.
- `24` test examples.
- `12` BM25-intended examples.
- `12` Dense-intended examples.
- `12` KG-intended examples.
- `12` Hybrid-intended examples.

Each item includes:

- `id`: stable example id.
- `query`: the user-facing question.
- `split`: `dev` or `test`.
- `intended_route_family`: one of `bm25`, `dense`, `kg`, or `hybrid`.
- `difficulty`: `hard` or `adversarial`.
- `ambiguity_tags`: one or more tags explaining why the case is hard.
- `gold_answer`: normalized expected answer.
- `gold_source_doc_ids`: source document ids where applicable.
- `gold_triple_ids`: KG/public-graph triple ids where applicable.
- `notes`: short explanation of the difficulty.

The builder grounds examples in existing local and public artifacts. It does not create a new production corpus and it does not replace any earlier benchmark.

## What Ambiguity Tags Mean

`lexical_semantic_overlap` means the query has both exact terms and conceptual phrasing, so BM25 and Dense can both look plausible.

`misleading_exact_term` means the query includes an exact phrase or identifier that is not the real answer target.

`identifier_with_distractor_language` means the query asks for an exact identifier but contains semantic wording that could distract the router.

`noisy_structure` means the query needs KG-style reasoning but includes text noise or misleading contextual words.

`wrong_bridge_distractor` means a relational query contains a plausible but wrong bridge entity or relation.

`top1_topk_gap_risk` means the right evidence may appear in top-k but not necessarily top-1.

`public_document_noise` means formatting, boilerplate, or public-source wording makes retrieval harder.

`route_boundary_ambiguity` means the query deliberately sits near the boundary between two or more route families.

`identifier_ambiguity` means multiple similar identifiers or identifier forms can compete.

## How Hard-Case Evaluation Works

The verifier loads the adversarial benchmark and builds a shared retrieval context from:

- noisy local corpus documents,
- public raw corpus documents,
- mixed demo KG and public graph triples.

It evaluates:

- `computed_ras`: the production PRISM router.
- `keyword_rule_router`: simple deterministic keyword rules.
- `classifier_router`: a local TF-IDF style classifier baseline trained on the curated benchmark labels for analysis.
- `random_router`: fixed-seed random routing.
- `always_bm25`: fixed BM25 backend.
- `always_dense`: fixed Dense backend.
- `always_kg`: fixed KG backend.
- `always_hybrid`: fixed Hybrid backend.

Metrics include:

- route accuracy,
- answer accuracy,
- evidence hit@k,
- top-1 evidence hit,
- top-1 versus top-k gap,
- per-family accuracy,
- per-ambiguity-tag accuracy,
- predicted-backend distribution,
- route confusion.

The key result is that computed RAS is not best on this adversarial benchmark. Computed RAS reached answer accuracy `0.729`, while `always_dense` reached `0.771` and `classifier_router` reached `0.792`. This is useful because it reveals route-boundary stress cases that earlier near-perfect benchmarks could not expose.

## How Confidence Analysis Works

The confidence layer reuses the existing route-confidence logic. For each computed RAS prediction, it looks at signals such as:

- the margin between the best and second-best RAS scores,
- agreement or disagreement with other router baselines,
- route rationale metadata.

The verifier groups examples into confidence buckets and compares misses by bucket. On the adversarial suite, low-confidence examples are more error-prone:

- low combined miss rate: `1.000`
- high combined miss rate: `0.324`

This is useful because earlier clean benchmarks were too close to perfect to show a clear confidence-to-error relationship.

## How Failure Analysis Works

The failure-analysis CLI reads `data/eval/adversarial_eval.json` and focuses on computed RAS misses. It assigns inspectable rule-assisted buckets such as:

- route boundary confusion,
- lexical over-trigger,
- semantic over-generalization,
- KG incompleteness,
- public-document noise,
- relational bridge confusion,
- identifier ambiguity,
- answer synthesis miss,
- evidence present in top-k but not top-1,
- retrieval miss.

The largest observed buckets were:

- route boundary confusion: `13`
- lexical over-trigger: `11`
- evidence present in top-k but not top-1: `10`
- answer synthesis miss: `8`

This means many hard-case failures are not simple lack-of-evidence failures. Several cases have the right evidence somewhere in top-k, but routing, ranking, or answer synthesis does not use it cleanly enough.

## Targeted Ablations

The adversarial verifier also writes a compact ablation summary.

The current targeted checks showed:

- Semantic rerank helped on hard cases: no-rerank answer accuracy `0.708` versus normal `0.729`.
- Public lexical arbitration hurt on this hard set: arbitrated answer accuracy `0.708` versus normal `0.729`.
- Public graph alone was weaker than mixed structure on the structure subset: `0.750` versus `0.833`.

These are analysis-only settings. They do not change the production demo path.

## What Artifacts Are Generated

The main artifacts are in `data/eval/`.

- `adversarial_eval.json`: full structured benchmark and system results.
- `adversarial_eval.csv`: flat per-system metrics for quick inspection.
- `adversarial_eval_summary.md`: report-ready summary with tables and takeaways.
- `adversarial_confidence.json`: route-confidence records and bucket stats.
- `adversarial_confidence_summary.md`: confidence-vs-error summary.
- `adversarial_ablation_summary.md`: targeted robustness variant comparison.
- `adversarial_failure_analysis.json`: per-example miss records and bucket assignments.
- `adversarial_failure_analysis_summary.md`: report-ready failure-analysis summary.
- `adversarial_baselines_by_tag.png`: performance by ambiguity tag.
- `adversarial_confidence_error_rate.png`: confidence bucket error plot.
- `adversarial_top1_topk_gap.png`: top-1 vs top-k evidence gap plot.

## Concepts And Topics Used

Adversarial benchmark means a benchmark intentionally designed to expose failure modes rather than to reflect average easy-case performance.

Route-boundary ambiguity means a query looks like it could belong to multiple retrieval families. For example, a query can mention a formal identifier while also asking a semantic paraphrase question.

Evidence hit@k means the correct supporting evidence appears somewhere in the top `k` retrieved items.

Top-1 evidence hit means the correct supporting evidence is the first retrieved item.

Top-1 versus top-k gap means the right evidence is available but not ranked first. This usually points to ranking or synthesis weakness rather than total retrieval failure.

Fixed-backend baseline means forcing every query through one backend, such as always Dense or always BM25, instead of using a router.

Router baseline means an alternative route selector used for comparison, such as keyword rules, a lightweight classifier, or random routing.

Confidence calibration means checking whether the system's confidence level is actually predictive of correctness.

Ablation means disabling or swapping one component to see how much it contributes to performance.

Failure bucket means an interpretable category for a miss, such as lexical over-trigger or KG incompleteness.

## What Remains Unresolved

Computed RAS is not the strongest system on the new adversarial benchmark. This is expected and useful, but it means the router still has real boundary-case weaknesses.

Dense is unusually strong on several misleading-exact-term examples, which shows that some hard cases are better handled by semantic retrieval despite exact lexical bait.

The classifier router is strong on this suite, but it is an analysis baseline trained from curated labels and should not replace computed RAS without more careful validation.

Failure buckets are rule-assisted rather than human-labeled, so they should be treated as diagnostic categories, not final ground truth.

Answer matching is still string-based. Human evaluation would be better for nuanced answers, especially on relational and semantic hard cases.

The hard benchmark is small and hand-constructed. It is valuable for stress testing, but it should not be treated as a broad real-world prevalence estimate.
