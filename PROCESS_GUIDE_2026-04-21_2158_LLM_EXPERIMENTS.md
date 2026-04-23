# Process Guide: Optional Local LLM Experiments

## Basic Summary

This step added an optional local LLM experiment layer to PRISM. The purpose is to test whether a local LLM can help with route selection or answer/trace presentation on difficult cases, without replacing PRISM's representation-aware design.

The experiment is analysis-only. Computed RAS remains the production router, the deterministic answerer remains the default answer path, and the demo app behavior is unchanged.

## How The Local LLM Interface Works

The local LLM client lives in:

- `prism/llm_experiments/local_llm_client.py`

It currently supports an Ollama-compatible endpoint. By default it tries:

- provider: `ollama`
- model: `llama3.1:8b`
- endpoint: `http://127.0.0.1:11434/api/generate`

These can be changed with environment variables:

- `PRISM_LLM_PROVIDER`
- `PRISM_LLM_MODEL`
- `PRISM_OLLAMA_URL`
- `PRISM_LLM_TIMEOUT`

If the endpoint is unavailable, the client returns an unavailable response instead of crashing. This lets PRISM still generate report artifacts that honestly say LLM runtime results are missing.

## How LLM Routing Works

The LLM router lives in:

- `prism/llm_experiments/llm_router.py`
- `prism/llm_experiments/router_prompt.py`

The prompt gives the LLM:

- the query
- compact definitions of BM25, Dense, KG, and Hybrid
- parsed PRISM query features
- computed RAS scores
- optional evidence hints

The prompt tells the LLM not to answer the query. It must only choose the best route family and return JSON.

Expected output:

- `route`: one of `bm25`, `dense`, `kg`, `hybrid`
- `confidence`: number between 0 and 1
- `rationale`: short explanation
- `alternatives`: optional ranked alternative routes

This router is not used by the production pipeline unless a future analysis path explicitly opts into it.

## How Evidence-Grounded Refinement Works

The answer/trace refiner lives in:

- `prism/llm_experiments/answer_refiner.py`
- `prism/llm_experiments/trace_refiner.py`

It runs after the normal PRISM path has already produced:

- selected backend
- retrieved evidence
- deterministic structured answer
- deterministic reasoning trace

The LLM is only allowed to rewrite for readability using the supplied evidence. It must preserve:

- selected backend
- evidence ids
- evidence snippets
- route rationale

If the LLM is unavailable, the original deterministic answer and trace are returned unchanged.

## How LLM Evaluation Works

The verifier lives in:

- `prism/llm_experiments/verify_llm_router.py`

It compares:

- computed RAS
- calibrated rescue
- classifier router
- fixed backend baselines
- LLM router when available

It uses the existing calibrated-router artifacts for non-LLM baselines so it does not duplicate or change production logic. It reports results for:

- adversarial test
- curated benchmark
- generalization v2 test
- public raw test

If the LLM is unavailable, the verifier still writes JSON, CSV, Markdown, and plots. LLM metrics are marked as unavailable instead of being fabricated.

## How LLM-Vs-Human Comparison Works

The human comparison lives in:

- `prism/llm_experiments/compare_to_human_eval.py`

It reads:

- `data/human_eval/comparative_packet.json`
- `data/human_eval/comparative_annotations/`

When an LLM route is available, it checks whether the LLM route matches the route used by the human-majority preferred system output in each comparative item.

This is only an approximate alignment signal. It does not mean humans directly judged LLM-generated answers. A stronger future study would add LLM outputs to the comparative packet and ask evaluators to judge them directly.

## Artifacts Generated

Evaluation artifacts:

- `data/eval/llm_router_eval.json`
- `data/eval/llm_router_eval.csv`
- `data/eval/llm_router_eval_summary.md`
- `data/eval/llm_experiment_results_for_paper.md`

Plots:

- `data/eval/llm_router_comparison.png`
- `data/eval/llm_adversarial_tag_breakdown.png`

Human-alignment artifacts:

- `data/human_eval/llm_vs_human_summary.json`
- `data/human_eval/llm_vs_human_summary.md`

## What Remains Unresolved

The current environment did not allow access to the local Ollama endpoint, so LLM runtime metrics are not available yet. The next step is to run:

```bash
ollama serve
ollama pull llama3.1:8b
.venv/bin/python3 -m prism.llm_experiments.verify_llm_router
```

Then inspect:

- whether LLM route accuracy improves adversarial hard cases
- whether it hurts curated or public benchmarks
- whether LLM route choices align with human preferences
- whether evidence-grounded refinements improve readability without hurting faithfulness

## Concepts And Topics Used

Local LLM:

A model running on the user's machine rather than through a paid cloud API. In this repo, the first supported path is Ollama.

LLM router:

A router that asks a language model to choose BM25, Dense, KG, or Hybrid. It is an experimental baseline, not the production router.

Computed RAS:

The deterministic production route selector. It scores representation mismatch risk and selects the backend with the minimum RAS penalty.

Evidence-grounded generation:

The answer can only use retrieved evidence. The model is not allowed to inject outside knowledge.

Analysis-only mode:

A feature used for experiments and report artifacts, not for the default demo or production path.

Human preference alignment:

A comparison between model choices and the system outputs that human annotators preferred. This is useful but not the same as a direct human rating of new LLM outputs.
