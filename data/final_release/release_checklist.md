# Release Checklist

Release ready: `True`.
Production router: `computed_ras`.

## Readiness

- Class/project demo: `ready`
- Paper draft submission: `ready_with_caveats`
- Reproducibility handoff: `ready`

## Critical Components

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

## Release Package Components

- [x] final_project_overview: `data/final_release/final_project_overview.md`
- [x] paper_ready_summary: `data/final_release/paper_ready_summary.md`
- [x] demo_runbook: `data/final_release/demo_runbook.md`
- [x] demo_walkthrough_quick_reference: `data/final_release/demo_walkthrough_quick_reference.md`
- [x] ui_tour: `data/final_release/ui_tour.md`
- [x] ras_overview: `data/final_release/ras_overview.md`
- [x] ras_math_guide: `data/final_release/ras_math_guide.md`
- [x] ras_version_comparison: `data/final_release/ras_version_comparison.md`
- [x] ras_visual_explanation: `data/final_release/ras_visual_explanation.md`
- [x] ras_quick_reference: `data/final_release/ras_quick_reference.md`
- [x] reproducibility_runbook: `data/final_release/reproducibility_runbook.md`
- [x] central_claim_summary: `data/final_release/central_claim_summary.md`
- [x] artifact_manifest: `data/final_release/artifact_manifest.json`
- [x] known_results_summary: `data/final_release/known_results_summary.json`

## Optional Components

- [x] llm_experiments: `data/eval/llm_router_eval_summary.md`
- [x] ras_v4_vs_human: `data/human_eval/ras_v4_vs_human_summary.md`
- [x] ras_v4_vs_rescue: `data/eval/ras_v4_vs_rescue_summary.md`
- [x] release_plots_ras_v4: `data/eval/ras_v4_router_comparison.png`

## Analysis-Only Components

- `calibrated_rescue`
- `classifier_router`
- `ras_v3`
- `ras_v4`
- `optional_llm`

## Limitations

- RAS_V3 and RAS_V4 are not production replacements.
- Calibrated rescue is not the default production path.
- Open-corpus mode is bounded source-pack/local-corpus QA, not web-scale search.
- Optional local LLM results depend on local runtime availability.
