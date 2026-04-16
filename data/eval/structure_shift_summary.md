# Structure-Shift Evaluation Summary

This evaluation compares curated, extracted, and mixed KG modes without changing the production curated KG default.

## KG Artifacts

- Curated KG: `data/processed/kg_triples.jsonl` with 99 triples.
- Extracted KG: `data/processed/kg_extracted_triples.jsonl` with 21 triples.
- Mixed KG: 98 triples with provenance at `data/processed/kg_mixed_metadata.json`.

## Computed RAS By KG Mode

### Curated KG

- curated_deductive: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- curated_relational: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- generalization_v2_deductive: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- generalization_v2_relational: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.

### Extracted KG

- curated_deductive: answer_accuracy=0.750 (15/20), evidence_hit@k=0.650, route_accuracy=1.000.
- curated_relational: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- generalization_v2_deductive: answer_accuracy=0.700 (14/20), evidence_hit@k=0.850, route_accuracy=1.000.
- generalization_v2_relational: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.

### Mixed KG

- curated_deductive: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- curated_relational: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- generalization_v2_deductive: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.
- generalization_v2_relational: answer_accuracy=1.000 (20/20), evidence_hit@k=1.000, route_accuracy=1.000.

## Curated Vs Extracted Vs Mixed Delta

- curated_deductive/extracted: answer_delta=-0.250, evidence_delta=-0.350.
- curated_deductive/mixed: answer_delta=0.000, evidence_delta=0.000.
- curated_relational/extracted: answer_delta=0.000, evidence_delta=0.000.
- curated_relational/mixed: answer_delta=0.000, evidence_delta=0.000.
- generalization_v2_deductive/extracted: answer_delta=-0.300, evidence_delta=-0.150.
- generalization_v2_deductive/mixed: answer_delta=0.000, evidence_delta=0.000.
- generalization_v2_relational/extracted: answer_delta=0.000, evidence_delta=0.000.
- generalization_v2_relational/mixed: answer_delta=0.000, evidence_delta=0.000.

## Error Analysis

- Error buckets: {'KG incompleteness': 10, 'alias normalization failures': 1, 'extraction noise': 11, 'relation normalization failures': 5}.
- Common failure modes include KG incompleteness, extraction noise, alias normalization failures, relation normalization failures, and relational path degradation.

## Main Takeaways

- curated_deductive: curated=1.000, extracted=0.750, mixed=1.000 answer accuracy.
- curated_relational: curated=1.000, extracted=1.000, mixed=1.000 answer accuracy.
- generalization_v2_deductive: curated=1.000, extracted=0.700, mixed=1.000 answer accuracy.
- generalization_v2_relational: curated=1.000, extracted=1.000, mixed=1.000 answer accuracy.
- Largest answer degradation is -0.300 for extracted on generalization_v2_deductive.
- Curated KG remains the production default; extracted and mixed KG modes are analysis-only.

## Threats To Validity

- The extracted KG is rule-based and intentionally lightweight, not a full information-extraction system.
- Extraction is limited to patterns visible in the local corpus, so missing text causes missing triples.
- Relation normalization uses a small controlled predicate set and can miss paraphrases.
- Alias normalization is heuristic and handles only common demo entities.
- Curated and held-out benchmarks are grounded in local artifacts, not arbitrary web-scale evidence.

## Artifacts

- JSON: `data/eval/structure_shift.json`
- CSV: `data/eval/structure_shift.csv`
- Markdown: `data/eval/structure_shift_summary.md`
- Plot: `data/eval/structure_shift_kg_modes.png`
- Plot: `data/eval/structure_shift_degradation.png`
