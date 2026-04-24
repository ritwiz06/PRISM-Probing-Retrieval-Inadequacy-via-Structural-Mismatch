# Demo Walkthrough Quick Reference

This one-page sequence supports a compact live demonstration. Start in benchmark mode for the most reproducible path; switch to open-corpus mode only when source-pack behavior is part of the story.

Production router: `computed_ras`.

Research overlays: `calibrated_rescue`, `classifier_router`, `ras_v3`, `ras_v4`, and optional local LLM. These are comparison layers, not the production default.

## Live Sequence

1. **Production path**
   - Mode: `benchmark mode`
   - Preset: `Lexical: exact RFC identifier`
   - Show: query features, computed RAS scores, BM25 evidence, final answer
   - Narrative: Start with the default production router: computed RAS chooses the minimum-adequacy-risk backend.
2. **Representation contrast**
   - Mode: `benchmark mode`
   - Preset: `Semantic: paraphrased feeling`
   - Show: Dense evidence, alternate route table, answer trace
   - Narrative: Switch to a conceptual query to show that exact lexical matching is not enough.
3. **Structured reasoning**
   - Mode: `benchmark mode`
   - Preset: `Deductive: animal capability`
   - Show: KG evidence, structured trace, soundness note
   - Narrative: Show why deductive claims require graph-style evidence rather than only nearest text.
4. **Open-corpus workspace**
   - Mode: `source-pack mode`
   - Preset: `Open Corpus: source-pack climate anxiety`
   - Show: runtime corpus metadata, source pack provenance, query-local graph panel
   - Narrative: Move beyond fixed benchmarks while keeping the corpus bounded and reproducible.
5. **Research comparison**
   - Mode: `benchmark mode`
   - Preset: `Hard Case: misleading exact term`
   - Show: Compare Routers tab, RAS_V3/RAS_V4 status, calibrated rescue caveat
   - Narrative: Close with the honest research story: route adequacy matters, but hard cases still need evidence rescue.

## Safe Fallback

If source packs, optional LLM, URL fetching, or query-local graph extraction are unavailable, stay in benchmark mode and run:

`Lexical: exact RFC identifier`, `Semantic: paraphrased feeling`, `Deductive: animal capability`, `Relational: bridge path`

## Presentation Cues

- Show route scores before evidence so the audience understands the routing decision.
- Show evidence before answer so support and provenance remain visible.
- Keep the distinction clear: computed RAS is production; rescue, classifier, RAS_V3, RAS_V4, and LLM are research overlays.
- Open-corpus mode is bounded source-pack/local-corpus QA, not arbitrary web-scale search.
