# Public Structure Grounding Comparison

Source evaluation: `data/eval/public_graph_eval.json`.
Public graph triples: 49.
Benchmark total: 32.

## Structure-Mode Comparison

### Dev Split

- Demo KG answer accuracy: 1.000.
- Public graph answer accuracy: 1.000.
- Mixed public+demo answer accuracy: 1.000.
- Public graph delta vs demo: 0.000.
- Mixed delta vs public graph: 0.000.

- dev/hybrid: demo=1.000, public=1.000, mixed=1.000.
- dev/kg: demo=1.000, public=1.000, mixed=1.000.

### Test Split

- Demo KG answer accuracy: 1.000.
- Public graph answer accuracy: 1.000.
- Mixed public+demo answer accuracy: 1.000.
- Public graph delta vs demo: 0.000.
- Mixed delta vs public graph: 0.000.

- test/hybrid: demo=1.000, public=1.000, mixed=1.000.
- test/kg: demo=1.000, public=1.000, mixed=1.000.

## Interpretation

- dev: public_graph-only matches demo_kg answer accuracy; mixed_public_demo matches public_graph-only.
- test: public_graph-only matches demo_kg answer accuracy; mixed_public_demo matches public_graph-only.
- These deltas compare structure modes on a public-graph-grounded suite; they are not a claim that rule-based extraction solves arbitrary public KG construction.

## Threats To Validity

- The public graph is produced by lightweight rule/profile extraction, not a full information-extraction system.
- The public graph is small and source-selected, so it tests structure shift but not web-scale graph construction.
- Entity and relation normalization use controlled aliases and predicates that can miss public-text paraphrases.
- Public raw text is noisier than compact benchmark facts, and some facts may be absent after cleaning.
- Mixed public+demo performance should be interpreted as robustness with curated support still present, not solved public graph extraction.
- Answer matching is normalized string matching rather than human grading.

## Artifacts

- JSON: `data/eval/public_structure_comparison.json`
- Markdown: `data/eval/public_structure_comparison_summary.md`
