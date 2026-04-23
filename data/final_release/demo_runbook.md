# Demo Runbook

## Launch

```bash
.venv/bin/python3 -m streamlit run prism/demo/app.py
```

## Default Demo Rule

Keep the app in `benchmark mode` for the safest path. Production mode is `computed_ras`.

## Presenter Flow

1. Run `Lexical: exact RFC identifier` and show parsed query features, RAS scores, BM25 evidence, answer, and trace.
2. Run `Semantic: paraphrased feeling` and show Dense evidence.
3. Run `Deductive: animal capability` and show KG evidence.
4. Run `Relational: bridge path` and show Hybrid evidence.
5. Switch to `source-pack mode` with `Open Corpus: source-pack climate anxiety` if source packs are available.
6. Use `Hard Case: misleading exact term` to explain why calibrated rescue and RAS_V4 are research layers, not production replacements.

## Fallback

If source packs, optional LLM, URL fetching, or graph extraction are unavailable, use this safe sequence: Lexical: exact RFC identifier, Semantic: paraphrased feeling, Deductive: animal capability, Relational: bridge path.

## Presets

```json
[
  {
    "title": "Lexical: exact RFC identifier",
    "query": "RFC-7231",
    "expected_route": "bm25",
    "expected_evidence_source": "formal document chunk for RFC-7231",
    "presenter_note": "Shows why exact identifiers should route to BM25 rather than semantic similarity.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "lexical",
    "badge": "Exact ID"
  },
  {
    "title": "Lexical: medical code",
    "query": "What is ICD-10 J18.9?",
    "expected_route": "bm25",
    "expected_evidence_source": "formal ICD-style code snippet",
    "presenter_note": "Use this to show identifier extraction and exact-code grounding.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "lexical",
    "badge": "Code lookup"
  },
  {
    "title": "Semantic: paraphrased feeling",
    "query": "What feels like climate anxiety?",
    "expected_route": "dense",
    "expected_evidence_source": "semantic corpus chunk about climate anxiety",
    "presenter_note": "Shows semantic retrieval when the query is conceptual rather than identifier-heavy.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "semantic",
    "badge": "Conceptual"
  },
  {
    "title": "Semantic: rare paraphrase",
    "query": "What is an asphalt warmth pocket?",
    "expected_route": "dense",
    "expected_evidence_source": "semantic paraphrase chunk",
    "presenter_note": "Use this when explaining why Dense was upgraded to sentence-transformers + FAISS.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "semantic",
    "badge": "Paraphrase"
  },
  {
    "title": "Deductive: animal capability",
    "query": "Can a mammal fly?",
    "expected_route": "kg",
    "expected_evidence_source": "curated KG triples about mammal/bat/capability",
    "presenter_note": "Shows structured reasoning and why KG evidence is auditable.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "deductive",
    "badge": "KG"
  },
  {
    "title": "Deductive: universal scope",
    "query": "Are all mammals able to fly?",
    "expected_route": "kg",
    "expected_evidence_source": "KG support plus counterexample-style reasoning",
    "presenter_note": "Shows soundness handling for universal claims.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "deductive",
    "badge": "Universal"
  },
  {
    "title": "Relational: bridge path",
    "query": "What bridge connects bat and vertebrate?",
    "expected_route": "hybrid",
    "expected_evidence_source": "hybrid evidence combining text and graph path through mammal",
    "presenter_note": "Shows multi-hop/bridge reasoning and backend fusion.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "relational",
    "badge": "Bridge"
  },
  {
    "title": "Relational: dolphin and echolocation",
    "query": "What relation connects dolphin and echolocation?",
    "expected_route": "hybrid",
    "expected_evidence_source": "hybrid text and KG relation evidence",
    "presenter_note": "Shows relational lookup where both text support and structure matter.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "relational",
    "badge": "Relation"
  },
  {
    "title": "Open Corpus: source-pack climate anxiety",
    "query": "What feels like climate anxiety?",
    "expected_route": "dense",
    "expected_evidence_source": "wikipedia source pack",
    "presenter_note": "Switch to source-pack mode and show PRISM operating outside the fixed benchmark corpus.",
    "demo_mode": "source-pack mode",
    "safe_fallback": true,
    "category": "open-corpus",
    "badge": "Source pack"
  },
  {
    "title": "Open Corpus: local demo graph",
    "query": "What bridge connects bat and vertebrate?",
    "expected_route": "hybrid",
    "expected_evidence_source": "local demo folder query-local graph",
    "presenter_note": "Switch to local demo folder mode and show query-local graph extraction.",
    "demo_mode": "local demo folder mode",
    "safe_fallback": true,
    "category": "open-corpus",
    "badge": "Local graph"
  },
  {
    "title": "Hard Case: misleading exact term",
    "query": "Which concept feels like RFC-7231 but is about worry?",
    "expected_route": "dense",
    "expected_evidence_source": "adversarial hard-case context",
    "presenter_note": "Use this to explain the adversarial route-boundary weakness and why calibrated rescue is analysis-only.",
    "demo_mode": "benchmark mode",
    "safe_fallback": true,
    "category": "hard-case",
    "badge": "Boundary"
  }
]
```
