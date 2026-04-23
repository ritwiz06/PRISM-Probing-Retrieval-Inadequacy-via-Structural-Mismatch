# LLM Vs Human-Eval Summary

Status: `llm_unavailable`.
LLM provider/model: `ollama` / `llama3.1:8b`.
Available: `False`.

## Alignment
- LLM alignment could not be computed because the local LLM was unavailable.

## Setup Note
Local LLM runtime was unavailable. Start Ollama locally and set PRISM_LLM_MODEL if needed, then rerun `python -m prism.llm_experiments.verify_llm_router`. Error: <urlopen error [Errno 1] Operation not permitted>

## Caveat
This comparison maps LLM route choices to human-majority preferred system routes. It is useful for routing alignment, but it is not a direct human judgment of LLM-generated answers.
