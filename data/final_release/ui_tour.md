# PRISM UI Tour

The Streamlit app is organized as a polished research workspace.

## Executive Summary

This is the highest-level project view. It shows the thesis, architecture, benchmark profile, release posture, and strongest caveats with minimal text.

## Results at a Glance

This page condenses benchmark outcomes, adversarial caveats, calibrated-rescue gains, human evaluation, and open-corpus status into summary cards and charts.

## Guided Demo

This page presents a clean walkthrough of the main demonstration scenarios, with optional presenter notes hidden behind an explicit toggle.

## Demo / Query

The main production path. It is organized into four visible steps:

- Query + Corpus: shows the user query, selected source mode, and production-router reminder.
- Route Decision: shows computed RAS route scores, the selected backend, route margin, and benchmark route status where available.
- Evidence: shows ranked evidence cards with backend/source badges and provenance metadata.
- Answer + Trace: shows the final answer and structured reasoning trace.

## RAS Explainer

Explains what Representation Adequacy Score means, how `computed_ras`, `computed_ras_v2`, `ras_v3`, and `ras_v4` differ, and why calibrated rescue is an overlay rather than a production router. It includes a stepwise routing walkthrough, route-score charts, query-level feature inspection, version votes, and advisory ambiguity flags.

## Open Corpus

Shows bounded source-pack, local-folder, URL-list, or bundled local-demo runtime-corpus metadata. It reports document count, source types, index readiness, and query-local graph availability.

## Compare Routers

Shows production `computed_ras` beside research overlays: calibrated rescue, classifier router, RAS_V3, RAS_V4, and optional LLM routing if available.

## Evidence / Graph

Shows full ranked evidence, backend-specific metadata, and query-local graph/path evidence when extracted.

## Human Eval

Shows real standard and comparative annotation summaries, including evaluator count, packet sizes, human-score charts, and comparative preference tables.

## Results / Paper

Shows the final paper-facing story, benchmark snapshot, central claim, RAS_V4 caveats, and report artifacts.

## Empty-State Behavior

If optional artifacts are missing, the UI displays explanatory panels instead of blank sections. Benchmark mode remains the safe default.
