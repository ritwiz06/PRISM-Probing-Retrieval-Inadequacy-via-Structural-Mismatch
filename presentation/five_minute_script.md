# Five-Minute PRISM Script

## 0:00-0:30 - Title and Thesis

PRISM studies a specific retrieval problem: a question can fail because the system used the wrong representation. The core contribution is representation-aware routing. PRISM routes each query to BM25, Dense, KG, or Hybrid retrieval using computed RAS as the production router. My contribution was the production integration, routing and demo stability, final report, release package, and presentation deliverables. The other team members can fill in their own contribution details.

## 0:30-1:10 - Problem

A single retriever cannot preserve every kind of structure. Exact identifiers such as RFC numbers need lexical matching. Conceptual paraphrases need dense retrieval. Deductive questions need graph structure. Multi-hop bridge questions often need both text and structure. PRISM makes that choice explicit.

## 1:10-1:55 - KRR Insight

The KRR idea is structural mismatch. We represent the query type, reason about which representation is adequate, retrieve evidence from that backend, and expose a trace. This turns retrieval routing into a knowledge representation and reasoning decision rather than a hidden ranking detail.

## 1:55-2:50 - Architecture and RAS

The system parses features, scores route families, selects a backend, retrieves evidence, and generates an answer with provenance. The production router is computed_ras. RAS_V3 and RAS_V4 are analysis-only research variants. Calibrated rescue is also a research overlay and is not the production default.

## 2:50-4:00 - Evaluation and Results

PRISM is stable on the curated benchmark, external mini-benchmark, generalization_v2, public raw corpus, public graph benchmark, and open-corpus smoke checks. The adversarial benchmark is the hardest layer. computed_ras reaches 0.917 answer accuracy on adversarial test, while calibrated rescue reaches 0.958. This is the key lesson: route adequacy matters, but evidence adequacy also matters.

## 4:00-4:45 - Demo and Evidence Trace

In the UI, the demo shows the query, parsed features, route scores, selected backend, evidence ids, final answer, and reasoning trace. The same interface can compare production routing with research overlays.

## 4:45-5:00 - Takeaway

PRISM's main contribution is an inspectable representation-aware routing framework for structural mismatch. The honest limitation is that hard boundary cases still need better uncertainty and evidence rescue. Production remains computed_ras. Ritik's completed work covers production integration, routing/demo stability, final report, release package, and presentation deliverables; Omkar, Vaishnavi, and Moin can add their own contribution details.
