# RAS Quick Reference

Production router: `computed_ras`.

Research overlays: `computed_ras_v2`, `ras_v3`, `ras_v4`, `calibrated_rescue`, optional LLM.

## What To Say In A Demo

- RAS estimates which representation is adequate for the query.
- `computed_ras` is the production router because it is deterministic and stable.
- RAS_V3 formalizes route adequacy with interpretable learned weights.
- RAS_V4 adds evidence adequacy, making the research story stronger.
- Calibrated rescue shows hard cases often need better use of top-k evidence, not only better route choice.

## What To Say In A Paper

PRISM's contribution is representation-aware routing. Route-only adequacy helps but is incomplete on adversarial hard cases. Joint route-and-evidence adequacy is the stronger research framing, while production remains conservative.

## Promotion Decision

computed_ras remains production; RAS_V3/RAS_V4/rescue remain research overlays.
