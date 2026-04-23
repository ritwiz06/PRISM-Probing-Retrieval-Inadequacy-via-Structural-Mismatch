# RAS V4 For Paper

RAS_V4 extends route-only RAS by scoring route adequacy and evidence adequacy jointly for every candidate backend.

## Why Route-Only RAS Was Insufficient

RAS_V3 improved adversarial route accuracy but did not improve adversarial answer accuracy. That failure mode showed that choosing a representation is not enough when the evidence returned by that representation is weak, noisy, or poorly ranked.

## How Evidence Adequacy Changes The Story

RAS_V4 inspects each backend's top-k evidence before choosing a final backend. It uses score gaps, lexical identifier matches, source/title overlap, KG path completeness, hybrid agreement, diversity, contamination, and answerability markers.

## Main Result

- Adversarial test computed RAS answer accuracy: 0.917.
- Adversarial test RAS_V4 answer accuracy: 0.917.
- Adversarial test RAS_V4+rescue answer accuracy: 0.958.
- Adversarial test calibrated rescue answer accuracy: 0.958.
- Promotion decision: `keep_analysis_only`.

## Interpretation

RAS_V4 remains analysis-only because at least one strict guardrail was not met.
RAS_V4 is more publishable as a research framework than route-only RAS because it formalizes evidence adequacy, but the current learned model is not strong enough to replace computed RAS in production.

## Threats To Validity

- Training data remains small and benchmark-shaped.
- Evidence features are lightweight heuristics rather than human judgments.
- Human alignment compares route choices to existing comparative preferences, not newly annotated RAS_V4 outputs.
- Calibrated rescue may still outperform because it changes evidence ordering after route selection.
