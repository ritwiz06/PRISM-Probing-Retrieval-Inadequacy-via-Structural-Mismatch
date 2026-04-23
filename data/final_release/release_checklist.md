# Release Checklist

Production router: `computed_ras`.

## Readiness

- Class/project demo: `ready`
- Paper draft submission: `ready_with_caveats`
- Reproducibility handoff: `ready`

## Critical Artifacts

- [x] curated_end_to_end: `data/eval/end_to_end_verification.json`
- [x] external_mini: `data/eval/external_generalization_summary.md`
- [x] generalization_v2: `data/eval/generalization_v2_summary.md`
- [x] structure_shift: `data/eval/structure_shift_summary.md`
- [x] public_raw: `data/eval/public_corpus_eval_summary.md`
- [x] public_graph: `data/eval/public_graph_eval_summary.md`
- [x] adversarial: `data/eval/adversarial_eval_summary.md`
- [x] calibration: `data/eval/calibrated_router_summary.md`
- [x] ras_v3: `data/eval/ras_v3_eval_summary.md`
- [x] ras_v4: `data/eval/ras_v4_eval_summary.md`
- [x] human_eval: `data/human_eval/human_eval_summary.md`
- [x] comparative_human_eval: `data/human_eval/comparative_summary.md`
- [x] open_corpus: `data/eval/open_workspace_summary.md`
- [x] report_artifacts: `data/eval/report/prism_report_summary.md`
- [x] demo_app: `prism/demo/app.py`

## Optional Artifacts

- [x] llm_experiments: `data/eval/llm_router_eval_summary.md`
- [x] ras_v4_vs_human: `data/human_eval/ras_v4_vs_human_summary.md`
- [x] ras_v4_vs_rescue: `data/eval/ras_v4_vs_rescue_summary.md`
- [x] release_plots_ras_v4: `data/eval/ras_v4_router_comparison.png`

## Limitations

- RAS_V3 and RAS_V4 remain analysis-only.
- Calibrated rescue is a research/demo comparison overlay unless explicitly enabled.
- Open-corpus mode is bounded source-pack/local-corpus QA, not web-scale QA.
