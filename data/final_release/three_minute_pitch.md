# Three Minute Pitch

PRISM addresses structural retrieval mismatch. Exact identifiers, conceptual paraphrases, deductive claims, and bridge/path questions do not all want the same representation. PRISM makes that explicit by routing to BM25, Dense, KG, or Hybrid evidence.

The production path uses `computed_ras`, a transparent deterministic router. Research overlays include calibrated rescue, classifier routing, RAS_V3, and RAS_V4. RAS_V3 formalizes route adequacy as an interpretable feature model, and RAS_V4 extends that to joint route-and-evidence adequacy.

Empirically, PRISM is very strong on curated, external, held-out, public raw, public graph, and open-corpus smoke settings. The main weakness remains hard adversarial route-boundary cases. On those cases, calibrated rescue still beats route-only learned RAS variants on answer accuracy. That is an honest result, and it changes the scientific story in a useful way: route adequacy is important, but answer support depends on evidence adequacy as well.

The final system is ready for demo, submission, and handoff. The repo now includes a polished UI, a release package, human-eval analysis, and a bounded open-corpus workspace. The production decision remains explicit and conservative: `computed_ras` stays production, and the overlays stay overlays.
