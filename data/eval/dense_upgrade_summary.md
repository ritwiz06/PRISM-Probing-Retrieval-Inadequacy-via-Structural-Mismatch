# Dense Upgrade Summary

Previous Dense backend: numpy_fallback.
Current Dense backend: numpy_fallback.
Model name: hashing-semantic-fallback.
FAISS active: False.
Chunk count: 148.
Fallback reason: Could not load sentence-transformers model sentence-transformers/all-MiniLM-L6-v2: RuntimeError: Cannot send a request, as the client has been closed..

## External Semantic Result

External semantic answer accuracy: 1.0.
External semantic correct: 8/8.

## Photosynthesis Paraphrase Check

Query: What concept turns daylight into carbohydrates?
Top hit: lex_postgres_jsonb_insert (PostgreSQL jsonb_insert).
Top hit score: 0.09128709137439728.

## Limitations

- If sentence-transformers cannot load locally, PRISM falls back to the deterministic numpy/hash backend.
- If FAISS is unavailable, sentence-transformers embeddings still use numpy similarity search.
- This summary reports observed local behavior; it does not hide semantic misses.
