from __future__ import annotations

import pandas as pd
import streamlit as st

from prism.app.pipeline import load_retrievers
from prism.demo.data import (
    DEMO_PRESETS,
    backend_detail_rows,
    build_demo_view_model,
    load_benchmark_queries,
)


st.set_page_config(page_title="PRISM Demo", page_icon="PRISM", layout="wide")


@st.cache_resource(show_spinner="Building local PRISM retrievers...")
def _cached_retrievers() -> dict[str, object]:
    return load_retrievers()


@st.cache_data(show_spinner=False)
def _cached_benchmarks() -> dict[str, list[dict[str, object]]]:
    return load_benchmark_queries()


def main() -> None:
    st.title("PRISM: Representation-Aware Retrieval Demo")
    st.caption("Local deterministic demo: computed RAS router, four retrieval backends, evidence, answer, and reasoning trace.")

    benchmarks = _cached_benchmarks()
    selected_gold: dict[str, object] | None = None

    with st.sidebar:
        st.header("Demo Query")
        preset_label = st.selectbox("Preset examples", [label for label, _ in DEMO_PRESETS])
        preset_query = dict(DEMO_PRESETS)[preset_label]
        query = st.text_area("Query", value=preset_query, height=90)

        st.header("Benchmark Browser")
        slice_name = st.selectbox("Benchmark slice", list(benchmarks))
        slice_rows = benchmarks[slice_name]
        benchmark_query = st.selectbox("Stored query", [str(row["query"]) for row in slice_rows])
        if st.button("Use benchmark query"):
            selected_gold = next(row for row in slice_rows if row["query"] == benchmark_query)
            query = str(selected_gold["query"])
        else:
            selected_gold = next((row for row in slice_rows if row["query"] == query), None)

        run = st.button("Run PRISM", type="primary")

    if not run:
        st.info("Choose a preset or benchmark query, then run PRISM.")
        return

    view_model = build_demo_view_model(query, gold=selected_gold, retrievers=_cached_retrievers(), top_k=5)
    payload = view_model["payload"]
    answer = payload["answer"]

    _render_route_header(payload, view_model)
    _render_scores(view_model["score_rows"])
    _render_answer(answer)
    _render_evidence(view_model["evidence_rows"], backend_detail_rows(payload))
    _render_trace(payload["reasoning_trace"])
    _render_raw(payload, view_model)


def _render_route_header(payload: dict[str, object], view_model: dict[str, object]) -> None:
    cols = st.columns(4)
    cols[0].metric("Selected backend", str(payload["selected_backend"]).upper())
    cols[1].metric("Support score", f"{payload['answer']['support_score']:.3f}")
    gold_route = view_model.get("gold_route") or "not benchmark"
    cols[2].metric("Gold route", str(gold_route).upper())
    route_match = view_model.get("route_match")
    status = "n/a" if route_match is None else ("match" if route_match else "mismatch")
    cols[3].metric("Route status", status)


def _render_scores(rows: list[dict[str, object]]) -> None:
    st.subheader("RAS Route Scores")
    st.caption("Lower RAS is better. The computed router picks the minimum-RAS backend.")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    selected = next((row for row in rows if row["selected"]), None)
    if selected:
        st.success(f"Chosen backend: {selected['backend']} because it has the lowest RAS score.")


def _render_answer(answer: dict[str, object]) -> None:
    st.subheader("Final Answer")
    st.write(answer["final_answer"])
    st.caption(f"Answer type: {answer['answer_type']} | Rationale: {answer['route_rationale']}")


def _render_evidence(evidence_rows: list[dict[str, object]], detail_rows: list[dict[str, object]]) -> None:
    st.subheader("Retrieved Evidence")
    for row in evidence_rows:
        with st.expander(f"#{row['rank']} {row['id']} | score={row['score']:.4f} | type={row['type']}", expanded=row["rank"] == 1):
            st.write(row["snippet"])
            st.json(row["metadata"])

    st.subheader("Backend-Specific Evidence Metadata")
    st.caption("This panel exposes BM25 rank/score metadata, Dense chunk metadata, KG query mode/triples/paths, and Hybrid fusion metadata when present.")
    st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)


def _render_trace(trace: list[dict[str, object]]) -> None:
    st.subheader("Reasoning Trace")
    for step in trace:
        with st.expander(str(step.get("step", "trace step")), expanded=False):
            st.json(step)


def _render_raw(payload: dict[str, object], view_model: dict[str, object]) -> None:
    with st.expander("Raw demo payload"):
        st.json({"gold_route": view_model.get("gold_route"), "gold_answer": view_model.get("gold_answer"), "payload": payload})


if __name__ == "__main__":
    main()
