# PROCESS GUIDE 2026-04-22 19:07 - RAS UI Presentation Polish

## Basic summary
This pass improves the presentation quality of the RAS Explainer and Guided Demo UI without changing PRISM's routing behavior, benchmarks, or scientific claims. The production router remains `computed_ras`; RAS_V3, RAS_V4, classifier routing, optional LLM routing, and calibrated rescue remain research overlays.

## What was visually wrong before
The RAS explainer page had the right content but the wrong presentation style:
- too much explanatory text appeared directly on the page
- some copy sounded like internal presentation instructions
- RAS formulas were shown as raw text/code blocks
- long pseudo-formulas could clip or require horizontal scrolling
- the math layer did not look like a polished research explanation
- guided demo content mixed audience-facing material with speaker notes

## What improved in the audience-facing experience
The `RAS Explainer` page now uses a clearer hierarchy:
- RAS explainer hero
- why routing matters
- RAS family overview
- mathematical layer
- routing walkthrough
- query-level explanation
- sensitivity and robustness

The `Guided Demo` page now defaults to a polished audience-facing view. It shows the demonstration scenarios, route/evidence focus, production default, research overlay status, and bounded-corpus scope without exposing internal narration as the primary content.

## How formulas are now rendered
The Streamlit RAS page uses `st.latex` for the key equations.

`computed_ras` is shown as a penalty model:

$$
p_r(x)=1+\Delta_r^{lex}(x)+\Delta_r^{sem}(x)+\Delta_r^{ded}(x)+\Delta_r^{rel}(x)
$$

$$
\hat r=\arg\min_{r\in R}p_r(x)
$$

RAS_V3 is shown as a linear route-scoring model:

$$
s_r(x)=b_r+\sum_j w_{rj}f_j(x)
$$

$$
\hat r_{v3}=\arg\max_{r\in R}s_r(x)
$$

RAS_V4 is shown as joint route/evidence adequacy:

$$
z_r(x)=b+\sum_j\alpha_j q_j(x,r)+\sum_k\beta_k e_k(E_r(x),x)
$$

$$
\hat r_{v4}=\arg\max_{r\in R}z_r(x)
$$

The notation glossary is collapsible and explains query `x`, route `r`, features, evidence set, scores, and margin.

## How the guided demo was cleaned up
The guided demo now has an audience-facing default:
- concise top cards for production path, research overlays, and bounded scope
- scenario cards with focus areas
- reliable benchmark sequence
- workspace map

Presenter narration appears only when the `Presenter view` checkbox is enabled. This keeps the default page clean while preserving live-demo support.

## Presenter-mode behavior
Presenter mode is lightweight and local to the Guided Demo page. It reveals `Presenter notes` expanders under each scenario. It does not change any routing, evaluation, or app state.

## What remains unresolved
- This pass does not create new empirical results.
- RAS_V3 and RAS_V4 are still analysis-only.
- Calibrated rescue remains stronger than RAS_V4 on adversarial answer accuracy.
- The app still relies on Streamlit's standard chart and MathJax rendering rather than a custom front-end.
- Open-corpus mode remains bounded source-pack/local-corpus QA, not arbitrary web-scale QA.

## Concepts and topics used
- presentation hierarchy
- audience-facing copy
- presenter-only notes
- LaTeX math rendering
- route adequacy
- evidence adequacy
- production router vs research overlay
- bounded-corpus QA
- route-score visualization
- sensitivity and robustness summaries
