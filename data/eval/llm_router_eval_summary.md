# LLM Router Experiment Summary

Status: `llm_unavailable`.
Local LLM provider/model: `ollama` / `llama3.1:8b`.
Runtime available: `False`.
Runtime error: `<urlopen error [Errno 1] Operation not permitted>`.

## Automatic Benchmark Results
- adversarial_test: computed RAS answer=0.9166666666666666, calibrated/rescue answer=0.9583333333333334, classifier answer=0.875, LLM answer=None.
- curated: computed RAS answer=1.0, calibrated/rescue answer=1.0, classifier answer=1.0, LLM answer=None.
- generalization_v2_test: computed RAS answer=1.0, calibrated/rescue answer=1.0, classifier answer=1.0, LLM answer=None.
- public_raw_test: computed RAS answer=1.0, calibrated/rescue answer=1.0, classifier answer=1.0, LLM answer=None.

## Human Preference Alignment
- LLM-vs-human status: `llm_unavailable`.
- Alignment unavailable until local LLM route choices are generated.

## Tradeoffs
- Local LLM runtime was unavailable, so no LLM metric claims are made.
- The harness still compares non-LLM baselines and writes setup guidance for rerunning with Ollama.
- Computed RAS remains the production router; LLM behavior is optional and analysis-only.
