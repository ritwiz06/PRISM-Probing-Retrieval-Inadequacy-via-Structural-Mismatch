# Public Robustness Summary

- Previous public raw test answer accuracy: 0.917.
- Current computed RAS public raw test answer accuracy: 1.000.
- Public-arbitrated public raw test answer accuracy: 1.000.
- Before/after answer result: improved.
- Previous public raw test route accuracy: 0.875.
- Current computed RAS public raw test route accuracy: 0.917.
- Public-arbitrated route accuracy: 1.000.

## What Changed

- Feature parser marker matching now uses token boundaries to avoid accidental KG routing from substrings like `class` inside `dataclasses` or `eats` inside `threats`.
- Public documents now have companion enriched metadata with identifiers, aliases, lead summaries, headings, source URLs, and fetch status.
- Public-aware BM25 can boost title, alias, and identifier matches in public-corpus analysis mode.
- Public route arbitration is analysis-only and only overrides to BM25 for identifier-heavy queries with high public lexical confidence.

## Tradeoffs

- Public test answer accuracy improved from the Prompt 17 reference 0.917 to current computed RAS 1.000.
- Public lexical arbitration improves test route accuracy from 0.917 to 1.000.
- The main production-safe change is fixing substring marker false positives in feature parsing.
- The public lexical retriever and arbitration mode remain analysis-only and do not change the demo path by default.
