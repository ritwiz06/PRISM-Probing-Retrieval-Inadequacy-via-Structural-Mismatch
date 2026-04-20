# Adversarial Route Confidence

Confidence uses computed RAS margin plus agreement with keyword and classifier routers.

Total examples: 48.
Correlation statement: Low confidence is more error-prone on hard cases: low combined miss rate=1.000, high combined miss rate=0.324.

| Confidence | Total | Route miss rate | Answer miss rate | Evidence miss rate |
| --- | ---: | ---: | ---: | ---: |
| high | 34 | 0.176 | 0.147 | 0.029 |
| low | 3 | 0.667 | 0.333 | 0.333 |
| medium | 11 | 0.455 | 0.636 | 0.273 |

## Lowest-Confidence Examples

- `adv_bm25_dev_06` kg vs dense; label=low, score=0.1, query=Which sklearn class makes raw documents into TF-IDF features even though the query says topic meaning and semantic search?
- `adv_hybrid_test_06` hybrid vs bm25; label=low, score=0.1, query=What relation connects bat and fly, not the exact torch.nn.CrossEntropyLoss API?
- `adv_kg_dev_01` bm25 vs kg; label=medium, score=0.15, query=Under the closed-world demo structure, can a mammal fly despite RFC-7231 also mentioning methods?
- `adv_hybrid_dev_01` hybrid vs bm25; label=medium, score=0.25, query=What bridge connects bat and vertebrate when RFC-7231 also says routing?
- `adv_hybrid_dev_05` hybrid vs bm25; label=medium, score=0.25, query=What relation connects mammal and milk while HIPAA 164.512 appears as irrelevant boilerplate?
- `adv_dense_test_04` bm25 vs dense; label=low, score=0.3, query=What view of word meaning uses nearby contexts even though the query says lexical identifier?
- `adv_kg_dev_03` kg vs dense; label=medium, score=0.4, query=Is a bat a mammal or just a semantic article about flight?
- `adv_dense_dev_01` bm25 vs dense; label=medium, score=0.45, query=Which concept feels like RFC-7231 for emotions: worry or grief about climate futures?
- `adv_dense_dev_06` bm25 vs dense; label=medium, score=0.45, query=Which concept captures unfair automated outputs even when civil rights §1983 appears in the wording?
- `adv_hybrid_dev_04` hybrid vs dense; label=medium, score=0.5, query=What bridge connects salmon and vertebrate, not the semantic concept water cycle?
