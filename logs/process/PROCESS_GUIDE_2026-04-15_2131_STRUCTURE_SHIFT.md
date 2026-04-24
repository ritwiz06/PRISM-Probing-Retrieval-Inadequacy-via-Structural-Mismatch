# Process Guide: Extracted KG And Structure Shift

## Basic Summary

This task added a structure-shift evaluation layer for PRISM. The goal is to test what happens when the KG is no longer the compact curated graph that PRISM was built around.

The production system still uses the curated KG by default. The new extracted and mixed KG modes are analysis-only. They let us ask:

- How much does performance drop when KG facts are extracted from text by simple rules?
- Does mixing extracted triples with curated triples preserve performance while adding realism and provenance?

The result is honest: extracted-only KG hurts deductive reasoning. Mixed KG recovers curated performance.

## How Extracted KG Is Built

The extracted KG code lives in:

- `prism/kg_extraction/entity_normalization.py`
- `prism/kg_extraction/extract_triples.py`
- `prism/kg_extraction/build_extracted_kg.py`

The builder command is:

```bash
.venv/bin/python3 -m prism.kg_extraction.build_extracted_kg
```

It reads the local clean corpus:

- `data/processed/corpus.jsonl`

and writes:

- `data/processed/kg_extracted_triples.jsonl`
- `data/processed/kg_extracted.ttl`
- `data/processed/kg_extracted_metadata.json`

The extractor is rule-based. It looks for simple textual patterns such as:

- `X is a Y`
- `X is capable of Y`
- `X eats Y`
- `X has property Y`
- `X produces Y`
- `X connects to Z through Y`

The final extracted KG in this run contains `21` triples.

## How Entities And Relations Are Normalized

Entity normalization lives in:

- `prism/kg_extraction/entity_normalization.py`

It maps common aliases to canonical entity names. Examples:

- `bats` -> `bat`
- `mammals` -> `mammal`
- `mosquitoes` -> `mosquito`
- `flight` -> `fly`

Relation normalization maps text phrases to a small predicate set:

- `is a` -> `is_a`
- `capable of` -> `capable_of`
- `has property` -> `has_property`
- `eats` -> `eats`
- `produces` -> `produces`

The extractor intentionally keeps only known PRISM KG entities. This avoids many bad triples from general semantic text, but it also means unfamiliar entities are ignored.

## How KG Modes Differ

PRISM can now evaluate three KG modes:

- `curated`: the existing hand-built KG from `data/processed/kg_triples.jsonl`.
- `extracted`: only the automatically extracted KG from `data/processed/kg_extracted_triples.jsonl`.
- `mixed`: curated plus extracted triples.

The demo and production path still use `curated`.

Mixed mode deduplicates triples by:

- subject,
- predicate,
- object.

If a curated triple and extracted triple overlap, the curated triple id is preserved for compatibility, but provenance is recorded in:

- `data/processed/kg_mixed_metadata.json`

KG retrieval metadata now also includes `kg_mode` and triple provenance fields where relevant.

## How Structure-Shift Evaluation Works

The verifier lives in:

- `prism/kg_extraction/verify_structure_shift.py`

Run it with:

```bash
.venv/bin/python3 -m prism.kg_extraction.verify_structure_shift
```

It evaluates three KG modes:

- curated,
- extracted,
- mixed.

It evaluates four datasets:

- curated deductive slice,
- curated relational slice,
- held-out generalization v2 deductive items,
- held-out generalization v2 relational items.

It reports:

- route accuracy,
- answer accuracy,
- evidence hit@k,
- deductive accuracy,
- relational accuracy,
- extracted-vs-curated deltas,
- mixed-vs-curated deltas,
- error buckets.

## What The Results Mean

Computed RAS answer accuracy:

- Curated deductive: `1.000`
- Extracted deductive: `0.750`
- Mixed deductive: `1.000`
- Generalization v2 deductive with curated KG: `1.000`
- Generalization v2 deductive with extracted KG: `0.700`
- Generalization v2 deductive with mixed KG: `1.000`

The extracted KG loses deductive performance because it misses facts and counterexamples that the curated KG explicitly includes. That is expected and useful: it shows PRISM depends on structure quality for deductive queries.

Relational extracted-only accuracy stays high because Hybrid can use text evidence along with extracted structure. This is a different claim: Hybrid can be more robust when structured evidence is incomplete, as long as useful text evidence is still present.

## What Artifacts Are Generated

Extracted KG artifacts:

- `data/processed/kg_extracted_triples.jsonl`
- `data/processed/kg_extracted.ttl`
- `data/processed/kg_extracted_metadata.json`
- `data/processed/kg_mixed_metadata.json`

Structure-shift evaluation artifacts:

- `data/eval/structure_shift.json`
- `data/eval/structure_shift.csv`
- `data/eval/structure_shift_summary.md`
- `data/eval/structure_shift_kg_modes.png`
- `data/eval/structure_shift_degradation.png`

## Concepts And Topics Used

- KG: a knowledge graph, storing facts as subject-predicate-object triples.
- Extracted KG: a graph built from text using automatic or semi-automatic extraction.
- Curated KG: a hand-built graph designed for correctness and coverage.
- Mixed KG: a graph that combines curated and extracted facts.
- Structure shift: performance change when the structured representation changes quality, coverage, or noise level.
- Entity normalization: mapping aliases like `bats` to canonical names like `bat`.
- Relation normalization: mapping text phrases like `is capable of` to controlled predicates like `capable_of`.
- Provenance: metadata that says where a triple came from.
- Evidence hit@k: whether the retrieved evidence contains the gold fact or enough matching support.
- Deductive degradation: a drop in KG reasoning performance caused by missing or noisy triples.

## What Remains Unresolved

- Rule-based extraction is narrow and brittle.
- The local corpus is too small to support broad KG extraction.
- Universal claims require explicit counterexamples; extracted text rarely supplies them reliably.
- Alias normalization only covers common PRISM demo entities.
- Relation normalization does not yet handle many paraphrases.
- Mixed mode is useful for robustness analysis, but it does not prove extracted KG quality by itself because curated triples remain available.
