# Process Guide: Prompt 9 Analysis, Ablations, Claim Validation, and Report Artifacts

## Basic Summary

This step added PRISM’s results layer. The code now evaluates baselines, validates the project claims, runs ablations, and exports files that can be used directly in a report or presentation.

## How Baseline Evaluation Works

Baseline evaluation is implemented in `prism/analysis/evaluation.py`.

The evaluator loads the same 80-query combined benchmark used by the end-to-end verifier:

- 20 lexical queries.
- 20 semantic queries.
- 20 deductive queries.
- 20 relational queries.

It evaluates multiple systems:

- `computed_ras`: the production PRISM router.
- `always_bm25`: forces every query to BM25.
- `always_dense`: forces every query to Dense.
- `always_kg`: forces every query to KG.
- `always_hybrid`: forces every query to Hybrid.
- `random_router`: chooses a backend with a fixed random seed.
- `oracle_route`: uses the gold route label.

Each system is scored on:

- Route accuracy.
- Evidence hit@k.
- Normalized answer match.
- Per-slice performance.
- Overall combined performance.

The key comparison is whether computed RAS can route each query family to the representation that fits it better than one fixed backend can.

## What Ablations Were Run

Ablations are implemented in `prism/analysis/run_ablations.py`.

The ablations focus on Hybrid retrieval because Hybrid is the backend that fuses multiple evidence types.

The current ablations are:

- `hybrid_no_kg`: Hybrid uses Dense and BM25 but no KG.
- `hybrid_no_bm25`: Hybrid uses Dense and KG but no BM25.
- `hybrid_no_dense`: Hybrid uses KG and BM25 but no Dense.

The main measured impact is relational evidence hit@k. This is where Hybrid matters most because relational queries need both structure and text grounding.

In the current local benchmark, removing KG breaks relational all-gold evidence matching. Removing BM25 or Dense does not break it because either text backend can still supply the text evidence side for these curated examples.

## How Claim Validation Is Defined In This Repo

Claim validation is implemented in `prism/analysis/claim_validation.py`.

The claims are not philosophical statements; they are local benchmark checks with explicit metrics.

The checks are:

- Lexical queries favor BM25 over Dense if BM25 has higher lexical slice evidence hit@k.
- Semantic queries favor Dense over BM25 if Dense has higher semantic slice evidence hit@k.
- Deductive queries favor KG over Dense and BM25 if KG has higher deductive slice evidence hit@k than both.
- Relational queries favor Hybrid over single backends if Hybrid has higher relational slice evidence hit@k than BM25, Dense, and KG.
- Computed RAS beats or matches strong fixed-backend baselines overall if its answer accuracy is at least the best fixed backend’s answer accuracy.

If a claim fails, the code reports it as unsupported. The check is not weakened silently.

## What Artifacts Are Generated And Where

The report artifact CLI is:

```bash
.venv/bin/python3 -m prism.analysis.report_artifacts
```

It writes files to:

```text
data/eval/report/
```

Generated JSON files include:

- `data/eval/claim_validation.json`
- `data/eval/ablation_results.json`
- `data/eval/report/prism_report_summary.json`
- `data/eval/report/artifact_manifest.json`

Generated CSV files include:

- `data/eval/report/baseline_comparison.csv`
- `data/eval/report/per_slice_backend_comparison.csv`
- `data/eval/report/ablation_impacts.csv`
- `data/eval/report/claim_validation.csv`

Generated Markdown includes:

- `data/eval/report/prism_report_summary.md`

Generated plots include:

- `data/eval/report/overall_baseline_comparison.png`
- `data/eval/report/per_slice_backend_performance.png`
- `data/eval/report/predicted_backend_distribution.png`
- `data/eval/report/ablation_impact.png`

The plots use matplotlib only and force the headless `Agg` backend so they can be saved in CLI and test environments.

## What The Current Results Show

Computed RAS achieved route accuracy 1.000 and answer accuracy 1.000 on the combined 80-query local benchmark.

The strongest fixed-backend answer baseline was always Hybrid at 0.550 answer accuracy.

The local claim validation reported all five major PRISM claims as supported.

The strongest ablation finding was that removing KG from Hybrid drops relational evidence hit@k from 1.000 to 0.000 under the current all-gold-evidence criterion.

## What Remains Limited About The Experimental Setup

The benchmark is curated and small. It is useful for demonstrating the thesis, but it is not a large external benchmark.

The answer metric is normalized exact match and token overlap. It is deterministic and local, but it is not a substitute for expert human evaluation.

The oracle route is an upper bound because it uses the gold labels.

The random router uses one fixed seed for reproducibility. Other seeds could produce different random-baseline results.

The plots are simple report artifacts. They are meant to be useful for slides and notes, not publication-ready visual design.

## Concepts And Topics Used

Baseline means a comparison system used to contextualize PRISM’s performance.

Ablation means removing one component and measuring the effect.

Claim validation means turning a research claim into a measurable local benchmark check.

Evidence hit@k means the gold evidence appears in the top k retrieved results.

Route accuracy means the predicted backend matches the benchmark’s gold route label.

Normalized answer match means the evaluator normalizes text and checks whether the gold answer is sufficiently matched by the generated answer.

Oracle route means an upper-bound baseline that uses the gold route label instead of computing a route.

Fixed-backend baseline means every query is forced to one backend, such as always BM25 or always Dense.

Report artifact means a reusable output file for the final report or presentation, such as JSON, CSV, Markdown, or PNG.
