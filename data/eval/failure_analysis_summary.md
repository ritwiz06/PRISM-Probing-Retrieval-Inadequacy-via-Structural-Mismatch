# PRISM Failure Analysis

This report compares the reproducible numpy fallback, the real Dense backend before robustness reranking, and the current robust real Dense backend.

## Curated End-to-End Misses Before Robustness

- `Which idea is daylight carbohydrate alchemy?`: expected `Photosynthesis.`, got `Circadian rhythm. A circadian rhythm is an internal daily timing cycle that helps regulate sleep, hormones, alertness, and metabolism. [evidence: sem_circadian_rhythm::chunk_0]`; buckets=['answer_synthesis_miss', 'ranking_error', 'semantic_drift']; remediation=Gold evidence was present but under-ranked; use a narrow semantic alias/concept rerank rather than changing gold labels.
- `Which response is a benign trigger false alarm?`: expected `Allergy.`, got `Impostor syndrome. Impostor syndrome is persistent self-doubt where capable people feel like frauds despite evidence of competence. [evidence: sem_impostor_syndrome::chunk_0]`; buckets=['lexical_confusion', 'retrieval_miss', 'semantic_drift']; remediation=Gold evidence was absent from top-k; inspect semantic drift and add transparent reranking only if the query is already locally grounded.
- `Which idea is an internal metronome?`: expected `Circadian rhythm.`, got `Situated knowledge. Situated knowledge emphasizes that perspective, social position, and lived context shape what people observe and know. [evidence: sem_situated_knowledge::chunk_0]`; buckets=['answer_synthesis_miss', 'ranking_error', 'semantic_drift']; remediation=Gold evidence was present but under-ranked; use a narrow semantic alias/concept rerank rather than changing gold labels.

## Curated Semantic Ranking Changes

- `Which idea is daylight carbohydrate alchemy?`: competing evidence `sem_circadian_rhythm` -> robust top `sem_photosynthesis`.
- `Which response is a benign trigger false alarm?`: competing evidence `sem_impostor_syndrome` -> robust top `sem_allergy`.
- `Which idea is an internal metronome?`: competing evidence `sem_situated_knowledge` -> robust top `sem_circadian_rhythm`.

## External Photosynthesis Check

- Query: `What concept turns daylight into carbohydrates?`
- Fallback answer: `PostgreSQL jsonb_insert. PostgreSQL jsonb_insert inserts a new value into a JSONB document at a specified path. [evidence: lex_postgres_jsonb_insert::chunk_0]`
- Current answer: `Photosynthesis. Photosynthesis is the biological process where plants and other organisms convert sunlight, carbon dioxide, and water into stored chemical energy. [evidence: sem_photosynthesis::chunk_0]`
- Fixed now: `True`

## Artifacts

- JSON: `data/eval/failure_analysis.json`
- CSV: `data/eval/failure_analysis.csv`
- Dense before/after JSON: `data/eval/dense_before_after.json`
- Robustness summary: `data/eval/robustness_summary.md`
