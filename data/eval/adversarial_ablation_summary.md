# Adversarial Ablation Summary

| Variant | Total | Route accuracy | Answer accuracy | Evidence hit@k |
| --- | ---: | ---: | ---: | ---: |
| computed_ras | 48 | 0.729 | 0.729 | 0.896 |
| computed_ras_no_semantic_rerank | 48 | 0.729 | 0.708 | 0.875 |
| computed_ras_public_lexical_arbitrated | 48 | 0.708 | 0.708 | 0.833 |
| computed_ras_demo_kg_structure_subset | 24 | 0.958 | 0.833 | 0.917 |
| computed_ras_public_graph_structure_subset | 24 | 0.958 | 0.750 | 0.833 |
| computed_ras_mixed_structure_subset | 24 | 0.958 | 0.833 | 0.917 |

## Interpretation

- Semantic rerank delta: no_rerank answer accuracy 0.708 vs normal 0.729.
- Public lexical arbitration delta: arbitrated answer accuracy 0.708 vs normal 0.729.
- Structure subset public_graph answer accuracy 0.750 vs mixed 0.833.
