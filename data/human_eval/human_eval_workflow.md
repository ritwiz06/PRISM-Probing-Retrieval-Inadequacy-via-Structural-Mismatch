# Human Evaluation Workflow

## Standard Packet

1. Run `.venv/bin/python3 -m prism.human_eval.export_packets`.
2. Give evaluators `data/human_eval/eval_packet.md` and `data/human_eval/rubric.md`.
3. Copy `data/human_eval/annotation_template.csv` to `data/human_eval/annotations/<evaluator_id>.csv`.
4. Fill scores and rerun `.venv/bin/python3 -m prism.human_eval.analyze_annotations`.

## Comparative Packet

1. Run `.venv/bin/python3 -m prism.human_eval.export_comparative_packets`.
2. Give evaluators `data/human_eval/comparative_packet.md` and `data/human_eval/comparative_rubric.md`.
3. Copy `data/human_eval/comparative_annotation_template.csv` to `data/human_eval/comparative_annotations/<evaluator_id>.csv`.
4. Fill A/B/Tie choices and confidence scores.
5. Rerun `.venv/bin/python3 -m prism.human_eval.export_comparative_packets` or `.venv/bin/python3 -m prism.human_eval.compare_annotations`.

Do not edit benchmark gold labels or production routing based on annotations without a separate reviewed change.
