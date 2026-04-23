# Public Raw Vs Local Normalized Grounding

Local normalized source: `data/eval/generalization_v2.json`.
Public raw source: `data/eval/public_corpus_eval.json`.

## Overall Delta

- Local normalized test answer accuracy: 1.000.
- Public raw test answer accuracy: 0.875.
- Public-minus-local answer delta: -0.125.
- Local normalized test route accuracy: 0.950.
- Public raw test route accuracy: 0.917.
- Public-minus-local route delta: -0.033.

## Per-Family Delta

- bm25: answer delta 0.000, route delta -0.133, evidence delta 0.000.
- dense: answer delta -0.500, route delta 0.000, evidence delta -0.333.
- hybrid: answer delta 0.000, route delta 0.000, evidence delta 0.000.
- kg: answer delta 0.000, route delta 0.000, evidence delta 0.000.

## Diagnosis

- Overall answer accuracy delta public-minus-local is -0.125.
- Overall route accuracy delta public-minus-local is -0.033.
- Most degraded family is dense: answer delta -0.500, route delta 0.000, evidence delta -0.333.
- Retrieval/evidence grounding appears to explain more degradation than routing for the weakest family.

## Threats To Validity

- The local-normalized benchmark and public raw benchmark are different suites, so deltas are directional rather than paired-example effects.
- Public raw documents can be fetched, cached, or fallback snapshots depending on network availability.
- The public benchmark remains small and source-selected.
- Deductive and relational public results still use the compact demo KG for structured evidence.

## Artifacts

- JSON: `data/eval/public_vs_local_grounding.json`
- Markdown: `data/eval/public_vs_local_grounding_summary.md`
- Plot: `data/eval/public_vs_local_grounding_family_delta.png`
