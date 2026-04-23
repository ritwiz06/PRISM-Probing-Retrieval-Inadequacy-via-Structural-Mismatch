# RAS Overview

RAS means Representation Adequacy Score. In PRISM, RAS estimates which retrieval representation is structurally adequate for a query before the answer is generated.

The core thesis is simple: retrieval fails when the representation does not match the question. Exact identifiers are better served by BM25. Conceptual paraphrases are better served by Dense retrieval. Deductive membership or property questions need KG-style structure. Relational bridge questions often need Hybrid retrieval.

Production PRISM uses `computed_ras`, a deterministic penalty-table router. Later variants are research layers:

- `computed_ras_v2` adds narrow hard-case correction rules.
- `ras_v3` learns an interpretable route-adequacy score from features.
- `ras_v4` adds evidence-adequacy diagnostics to route adequacy.
- `calibrated_rescue` is an overlay showing that top-k evidence rescue is complementary to route choice.

The release decision remains explicit: production router = `computed_ras`. Learned and rescue layers are analysis/demo overlays.
