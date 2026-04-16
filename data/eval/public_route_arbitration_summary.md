# Public Route Arbitration

Policy: Analysis-only override to BM25 only when the query is identifier-heavy and public lexical confidence is high.

- Normal computed RAS test route accuracy: 0.917.
- Public-arbitrated test route accuracy: 1.000.
- Normal computed RAS test answer accuracy: 1.000.
- Public-arbitrated test answer accuracy: 1.000.

## Overrides

- dev / pub_bm25_03: `J18.9` dense -> bm25 with confidence 1.000.
- test / pub_bm25_11: `Python dataclasses generated special methods` dense -> bm25 with confidence 1.000.
- test / pub_bm25_12: `TfidfVectorizer raw documents matrix TF-IDF features` dense -> bm25 with confidence 1.000.
