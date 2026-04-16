# Public Graph Structural Grounding Evaluation

This evaluation compares PRISM's current demo KG with a graph extracted from public raw-document text and a mixed public+demo mode. The production demo default is unchanged.

## Public Graph

- Public graph triples: 49.
- Source documents represented: 20.
- Triple artifact: `data/processed/public_graph_triples.jsonl`.
- Turtle artifact: `data/processed/public_graph.ttl`.
- Metadata artifact: `data/processed/public_graph_metadata.json`.
- Extraction patterns: {'is_a': 1, 'source_profile': 48}.

## Benchmark

- Benchmark path: `data/processed/public_structure_benchmark.jsonl`.
- Benchmark total: 32.
- Benchmark counts: {'split': {'dev': 16, 'test': 16}, 'route_family': {'hybrid': 16, 'kg': 16}, 'provenance': {'public_graph': 32}}.
- Public-structure grounding coverage: {'total': 32, 'grounded': 32, 'coverage': 1.0, 'by_family': {'kg': {'total': 16, 'grounded': 16}, 'hybrid': {'total': 16, 'grounded': 16}}}.

## Computed RAS Results By Structure Mode

### Dev Split

- demo_kg: answer_accuracy=1.000 (16/16), evidence_hit@k=1.000, route_accuracy=1.000, distribution={'kg': 8, 'hybrid': 8}.
- public_graph: answer_accuracy=1.000 (16/16), evidence_hit@k=1.000, route_accuracy=1.000, distribution={'kg': 8, 'hybrid': 8}.
- mixed_public_demo: answer_accuracy=1.000 (16/16), evidence_hit@k=1.000, route_accuracy=1.000, distribution={'kg': 8, 'hybrid': 8}.

### Test Split

- demo_kg: answer_accuracy=1.000 (16/16), evidence_hit@k=1.000, route_accuracy=1.000, distribution={'kg': 8, 'hybrid': 8}.
- public_graph: answer_accuracy=1.000 (16/16), evidence_hit@k=1.000, route_accuracy=1.000, distribution={'kg': 8, 'hybrid': 8}.
- mixed_public_demo: answer_accuracy=1.000 (16/16), evidence_hit@k=1.000, route_accuracy=1.000, distribution={'kg': 8, 'hybrid': 8}.

## Demo KG Vs Public Graph Vs Mixed

- dev: public_graph answer delta vs demo=0.000; mixed answer delta vs demo=0.000; public evidence delta=0.000.
- dev/hybrid: demo=1.000, public=1.000, mixed=1.000.
- dev/kg: demo=1.000, public=1.000, mixed=1.000.
- test: public_graph answer delta vs demo=0.000; mixed answer delta vs demo=0.000; public evidence delta=0.000.
- test/hybrid: demo=1.000, public=1.000, mixed=1.000.
- test/kg: demo=1.000, public=1.000, mixed=1.000.

## Error Analysis

- Error buckets: {}.
- Public-graph-only errors, if present, are interpreted as structural brittleness rather than hidden by benchmark edits.

## Main Takeaways

- dev: demo_kg=1.000, public_graph=1.000, mixed_public_demo=1.000; public graph matches demo KG, mixed-minus-public=0.000.
- test: demo_kg=1.000, public_graph=1.000, mixed_public_demo=1.000; public graph matches demo KG, mixed-minus-public=0.000.
- Curated demo KG remains the production default; public_graph and mixed_public_demo are analysis modes.

## Threats To Validity

- The public graph is produced by lightweight rule/profile extraction, not a full information-extraction system.
- The public graph is small and source-selected, so it tests structure shift but not web-scale graph construction.
- Entity and relation normalization use controlled aliases and predicates that can miss public-text paraphrases.
- Public raw text is noisier than compact benchmark facts, and some facts may be absent after cleaning.
- Mixed public+demo performance should be interpreted as robustness with curated support still present, not solved public graph extraction.
- Answer matching is normalized string matching rather than human grading.

## Artifacts

- JSON: `data/eval/public_graph_eval.json`
- CSV: `data/eval/public_graph_eval.csv`
- Markdown: `data/eval/public_graph_eval_summary.md`
- Plot: `data/eval/public_graph_mode_performance.png`
- Plot: `data/eval/public_graph_dev_test_modes.png`
