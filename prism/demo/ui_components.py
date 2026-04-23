from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


ROUTE_COLORS: dict[str, str] = {
    "bm25": "#B45309",
    "dense": "#2563EB",
    "kg": "#047857",
    "hybrid": "#7C3AED",
    "computed_ras": "#0F766E",
    "calibrated_rescue": "#B45309",
    "classifier_router": "#4338CA",
    "ras_v3": "#0369A1",
    "ras_v4": "#BE123C",
    "optional_llm": "#64748B",
}


def inject_prism_theme() -> None:
    st.markdown(
        """
<style>
html, body, [class*="css"] {
  font-family: "Aptos", "Source Sans 3", "Helvetica Neue", sans-serif;
}
.block-container {
  padding-top: 2.0rem;
  padding-bottom: 3.0rem;
  max-width: 1320px;
}
h1, h2, h3 {
  letter-spacing: -0.035em;
}
div[data-testid="stMetric"] {
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  border: 1px solid #E2E8F0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
}
div[data-testid="stTabs"] button {
  border-radius: 999px;
  padding: 0.55rem 1.0rem;
}
.prism-hero {
  background: radial-gradient(circle at top left, rgba(20, 184, 166, 0.20), transparent 38%),
              linear-gradient(135deg, #0F172A 0%, #164E63 58%, #0F766E 100%);
  border-radius: 28px;
  color: white;
  padding: 2.0rem 2.2rem;
  margin-bottom: 1.2rem;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
}
.prism-hero h1 {
  font-size: 2.6rem;
  margin: 0 0 0.45rem 0;
}
.prism-hero p {
  color: rgba(255, 255, 255, 0.84);
  font-size: 1.05rem;
  line-height: 1.55;
  max-width: 920px;
  margin: 0;
}
.prism-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 20px;
  padding: 1.05rem 1.15rem;
  margin: 0.45rem 0 0.8rem 0;
  box-shadow: 0 10px 32px rgba(15, 23, 42, 0.055);
}
.prism-card.compact {
  padding: 0.85rem 0.95rem;
}
.prism-card-title {
  color: #0F172A;
  font-size: 1.02rem;
  font-weight: 760;
  margin-bottom: 0.35rem;
}
.prism-card-value {
  color: #0F172A;
  font-size: 1.7rem;
  font-weight: 800;
  letter-spacing: -0.035em;
  margin-bottom: 0.2rem;
}
.prism-card-caption {
  color: #64748B;
  font-size: 0.88rem;
  line-height: 1.45;
}
.prism-step {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  color: #0F172A;
  font-weight: 800;
  letter-spacing: -0.02em;
  font-size: 1.25rem;
  margin: 1.0rem 0 0.35rem 0;
}
.prism-step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 999px;
  background: #0F766E;
  color: white;
  font-size: 0.95rem;
}
.prism-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.25rem 0.62rem;
  font-size: 0.74rem;
  font-weight: 760;
  letter-spacing: 0.01em;
  margin: 0.1rem 0.2rem 0.1rem 0;
  border: 1px solid rgba(15, 23, 42, 0.08);
  white-space: nowrap;
}
.prism-evidence {
  border-left: 5px solid #0F766E;
  background: linear-gradient(90deg, #F0FDFA 0%, #FFFFFF 62%);
  border-radius: 16px;
  padding: 0.9rem 1rem;
  margin: 0.55rem 0;
}
.prism-muted {
  color: #64748B;
}
.prism-warning {
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  color: #92400E;
  border-radius: 16px;
  padding: 0.9rem 1rem;
  margin: 0.55rem 0;
}
.prism-info {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  color: #1E3A8A;
  border-radius: 16px;
  padding: 0.9rem 1rem;
  margin: 0.55rem 0;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
<div class="prism-hero">
  <h1>{escape(title)}</h1>
  <p>{escape(subtitle)}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_card(title: str, value: object, caption: str = "", *, compact: bool = False) -> None:
    class_name = "prism-card compact" if compact else "prism-card"
    st.markdown(
        f"""
<div class="{class_name}">
  <div class="prism-card-title">{escape(title)}</div>
  <div class="prism-card-value">{escape(str(value))}</div>
  <div class="prism-card-caption">{escape(caption)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_step(step: int, title: str, caption: str = "") -> None:
    st.markdown(
        f"""
<div class="prism-step">
  <span class="prism-step-number">{step}</span>
  <span>{escape(title)}</span>
</div>
<div class="prism-muted">{escape(caption)}</div>
        """,
        unsafe_allow_html=True,
    )


def badge(label: object, *, color: str = "#334155", background: str = "#F1F5F9") -> str:
    return (
        f'<span class="prism-badge" style="color:{color}; background:{background};">'
        f"{escape(str(label))}</span>"
    )


def route_badge(route: object) -> str:
    route_text = str(route).lower()
    color = ROUTE_COLORS.get(route_text, "#334155")
    return badge(str(route).upper(), color=color, background=_tint(color))


def mode_badge(mode: object) -> str:
    mode_text = str(mode)
    if mode_text == "computed_ras":
        return badge("PRODUCTION: computed_ras", color="#0F766E", background="#CCFBF1")
    color = ROUTE_COLORS.get(mode_text, "#64748B")
    return badge(f"RESEARCH: {mode_text}", color=color, background=_tint(color))


def render_badges(items: Iterable[str]) -> None:
    st.markdown(" ".join(items), unsafe_allow_html=True)


def render_info_card(message: str, *, warning: bool = False) -> None:
    class_name = "prism-warning" if warning else "prism-info"
    st.markdown(f'<div class="{class_name}">{escape(message)}</div>', unsafe_allow_html=True)


def evidence_card(rank: object, item_id: object, score: object, source_type: object, snippet: object, backend: object = "") -> None:
    backend_html = route_badge(backend) if backend else ""
    st.markdown(
        f"""
<div class="prism-evidence">
  <div>{backend_html} {badge(f"rank {rank}")} {badge(f"score {score}")} {badge(source_type)}</div>
  <div style="font-weight:760; margin-top:0.45rem;">{escape(str(item_id))}</div>
  <div style="color:#334155; line-height:1.55; margin-top:0.25rem;">{escape(str(snippet))}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _tint(hex_color: str) -> str:
    palette = {
        "#B45309": "#FEF3C7",
        "#2563EB": "#DBEAFE",
        "#047857": "#D1FAE5",
        "#7C3AED": "#EDE9FE",
        "#0F766E": "#CCFBF1",
        "#4338CA": "#E0E7FF",
        "#0369A1": "#E0F2FE",
        "#BE123C": "#FFE4E6",
        "#64748B": "#F1F5F9",
    }
    return palette.get(hex_color, "#F1F5F9")
