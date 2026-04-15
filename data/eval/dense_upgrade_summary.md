# Dense Upgrade Summary

Previous Dense backend: numpy_fallback.
Current Dense backend: sentence_transformers+faiss.
Model name: sentence-transformers/all-MiniLM-L6-v2.
FAISS active: True.
Chunk count: 148.
Fallback reason: none.

## External Semantic Result

External semantic answer accuracy: 1.0.
External semantic correct: 8/8.

## Photosynthesis Paraphrase Check

Query: What concept turns daylight into carbohydrates?
Top hit: sem_photosynthesis (Photosynthesis).
Top hit score: 0.46774813532829285.

## Limitations

- If sentence-transformers cannot load locally, PRISM falls back to the deterministic numpy/hash backend.
- If FAISS is unavailable, sentence-transformers embeddings still use numpy similarity search.
- This summary reports observed local behavior; it does not hide semantic misses.
