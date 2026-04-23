# RAS Visual Explanation

Use this sequence for slides, posters, or the Streamlit `RAS Explainer` page.

## Visual Story

1. Query arrives.
2. PRISM extracts route-relevant features: identifier-heavy, semantic abstraction, deductive cue, relational bridge cue, source context, and ambiguity signals.
3. Candidate routes receive scores.
4. The selected route retrieves evidence.
5. The answerer produces an evidence-cited answer and trace.
6. If margins are low or RAS variants disagree, PRISM surfaces an advisory ambiguity warning.

## How To Explain The Versions

- `computed_ras`: simple penalty table. Lower score wins.
- `computed_ras_v2`: computed RAS plus narrow rule corrections.
- `ras_v3`: learned but interpretable route-only score. Higher score wins.
- `ras_v4`: learned but interpretable joint route/evidence score. Higher score wins.
- `calibrated_rescue`: post-route rescue overlay, not the production router.

## Demo Guidance

Show route scores first, then evidence, then answer. This keeps PRISM's core distinction visible: route adequacy chooses the representation, evidence adequacy determines whether that route actually supports an answer.
