from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from prism.app.pipeline import load_retrievers
from prism.demo.data import (
    backend_detail_rows,
    build_demo_view_model,
    load_benchmark_queries,
)
from prism.demo.demo_script_data import demo_script_payload
from prism.demo.presets import (
    grouped_presets_payload,
    preset_by_title,
    presets_payload,
)
from prism.demo.ui_components import (
    badge,
    evidence_card,
    inject_prism_theme,
    mode_badge,
    render_badges,
    render_card,
    render_hero,
    render_info_card,
    render_mini_card,
    render_section_header,
    render_step,
    render_status_line,
    route_badge,
)
from prism.open_corpus.source_packs import list_source_packs
from prism.open_corpus.view_model import build_open_workspace_view_model
from prism.ras_explainer.version_compare import build_version_comparison, explain_query


st.set_page_config(page_title="PRISM Demo", page_icon="PRISM", layout="wide")
inject_prism_theme()


@st.cache_resource(show_spinner="Building local PRISM retrievers...")
def _cached_retrievers() -> dict[str, object]:
    return load_retrievers()


@st.cache_data(show_spinner=False)
def _cached_benchmarks() -> dict[str, list[dict[str, object]]]:
    return load_benchmark_queries()


@st.cache_data(show_spinner=False)
def _cached_json(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> None:
    render_hero(
        "PRISM Demo Workspace",
        "A representation-aware retrieval router for BM25, Dense, KG, and Hybrid evidence. "
        "The production path stays computed_ras; calibrated rescue, classifier routing, RAS_V3, RAS_V4, "
        "and optional LLM routing are explicitly labeled research overlays.",
    )

    benchmarks = _cached_benchmarks()
    selected_gold: dict[str, object] | None = None
    preset_groups = grouped_presets_payload()

    with st.sidebar:
        st.markdown("### Demo Controls")
        st.success("Production router: computed_ras")
        st.caption("Research overlays are visible for comparison, not silently promoted.")

        st.markdown("### Corpus / Source")
        corpus_mode = st.selectbox(
            "Workspace mode",
            ["benchmark mode", "source-pack mode", "local demo folder mode", "local folder mode", "URL list mode"],
            help="Benchmark mode is the default safe presentation path.",
        )
        source_pack = "wikipedia"
        local_folder = ""
        url_text = ""
        if corpus_mode == "source-pack mode":
            packs = list_source_packs()
            source_pack = st.selectbox("Source pack", packs, index=packs.index("wikipedia") if "wikipedia" in packs else 0)
        elif corpus_mode == "local folder mode":
            local_folder = st.text_input("Local folder path", value="data/runtime_corpora/local_demo_docs/raw")
        elif corpus_mode == "URL list mode":
            url_text = st.text_area(
                "Small URL list",
                value="",
                height=90,
                placeholder="https://example.org/page\nhttps://example.org/other",
            )
        st.caption("Open-corpus modes stay separate from fixed benchmark corpora.")

        st.markdown("### Preset Query")
        category = st.selectbox("Preset group", list(preset_groups))
        labels = [str(row["title"]) for row in preset_groups[category]]
        preset_label = st.selectbox("Preset", labels)
        preset = preset_by_title(preset_label)
        render_badges([badge(preset.badge), route_badge(preset.expected_route), badge(preset.demo_mode)])
        st.caption(f"Scenario: {preset.presenter_note}")
        query = st.text_area("Query", value=preset.query, height=92)

        st.markdown("### Benchmark Browser")
        slice_name = st.selectbox("Benchmark slice", list(benchmarks))
        slice_rows = benchmarks[slice_name]
        benchmark_query = st.selectbox("Stored query", [str(row["query"]) for row in slice_rows])
        if st.button("Use benchmark query"):
            selected_gold = next(row for row in slice_rows if row["query"] == benchmark_query)
            query = str(selected_gold["query"])
        else:
            selected_gold = next((row for row in slice_rows if row["query"] == query), None)

        run = st.button("Run PRISM", type="primary", use_container_width=True)

    tabs = st.tabs(
        [
            "Guided Demo",
            "RAS Explainer",
            "Demo / Query",
            "Open Corpus",
            "Compare Routers",
            "Evidence / Graph",
            "Human Eval",
            "Results / Paper",
        ]
    )
    tab_walkthrough, tab_ras, tab_query, tab_open, tab_compare, tab_evidence, tab_human, tab_results = tabs

    with tab_walkthrough:
        _render_guided_demo()
    with tab_ras:
        _render_ras_explainer(query)

    if not run:
        with tab_query:
            _render_demo_overview()
        with tab_open:
            _render_open_corpus_guidance()
        with tab_compare:
            _render_research_mode_guidance()
        with tab_evidence:
            render_info_card("Run a query to inspect ranked evidence and query-local graph details.")
        with tab_human:
            _render_human_eval_summary()
        with tab_results:
            _render_results_summary()
        return

    if corpus_mode == "benchmark mode":
        view_model = build_demo_view_model(query, gold=selected_gold, retrievers=_cached_retrievers(), top_k=5)
        payload = view_model["payload"]
        open_workspace = None
    else:
        source_mode = {
            "source-pack mode": "source_pack",
            "local demo folder mode": "local_demo",
            "local folder mode": "local_folder",
            "URL list mode": "url_list",
        }[corpus_mode]
        try:
            open_workspace = build_open_workspace_view_model(
                query,
                source_mode=source_mode,
                source_pack=source_pack,
                local_paths=[local_folder] if local_folder else None,
                urls=[line for line in url_text.splitlines() if line.strip()],
                top_k=5,
            )
        except Exception as exc:  # pragma: no cover - defensive UI guard
            with tab_query:
                render_info_card(f"Open-corpus workspace could not be built: {exc}", warning=True)
                render_info_card("Benchmark mode and the bundled local demo folder remain available as reliable fallback paths.")
            return
        payload = open_workspace
        view_model = _open_workspace_view_model(open_workspace)

    with tab_query:
        _render_main_query_flow(query, corpus_mode, payload, view_model)
    with tab_open:
        if open_workspace:
            _render_open_workspace(open_workspace)
        else:
            _render_open_corpus_guidance()
    with tab_compare:
        _render_router_comparison(open_workspace, payload)
    with tab_evidence:
        _render_evidence(view_model["evidence_rows"], backend_detail_rows(payload) if not open_workspace else view_model["backend_detail_rows"], payload)
        if open_workspace:
            _render_graph(open_workspace)
    with tab_human:
        _render_human_eval_summary()
    with tab_results:
        _render_results_summary()
        _render_raw(payload, view_model)


def _open_workspace_view_model(open_workspace: dict[str, object]) -> dict[str, object]:
    selected_backend = str(open_workspace["selected_backend"])
    return {
        "gold_route": None,
        "gold_answer": None,
        "route_match": None,
        "score_rows": [
            {"backend": backend, "ras_score": score, "selected": backend == selected_backend}
            for backend, score in sorted(open_workspace["ras_scores"].items(), key=lambda item: item[1])
        ],
        "evidence_rows": [
            {
                "rank": rank,
                "id": item.get("item_id"),
                "score": item.get("score"),
                "type": item.get("source_type"),
                "snippet": item.get("content"),
                "metadata": item.get("metadata", {}),
            }
            for rank, item in enumerate(open_workspace["top_evidence"], start=1)
        ],
        "backend_detail_rows": [
            {
                "evidence_id": item.get("item_id"),
                "source_type": item.get("source_type"),
                "score": item.get("score"),
                "metadata": item.get("metadata", {}),
            }
            for item in open_workspace["top_evidence"]
        ],
    }


def _render_main_query_flow(query: str, corpus_mode: str, payload: dict[str, object], view_model: dict[str, object]) -> None:
    render_step(1, "Query + Corpus", "Start with the user question and the bounded evidence source.")
    cols = st.columns([2, 1, 1])
    with cols[0]:
        render_card("Query", query, "The selected corpus determines what PRISM can cite.")
    with cols[1]:
        render_card("Corpus mode", corpus_mode, "Benchmark mode is the safest live-demo path.")
    with cols[2]:
        render_card("Production router", "computed_ras", "Research overlays are comparison-only.")
    parsed_features = payload.get("parsed_features", {})
    with st.expander("Parsed query features", expanded=False):
        st.json(parsed_features)

    render_step(2, "Route Decision", "Computed RAS chooses the minimum-risk backend. Lower RAS is better.")
    _render_route_header(payload, view_model)
    _render_scores(view_model["score_rows"])
    _render_query_level_ras_inspection(query)

    render_step(3, "Evidence", "Evidence is ranked, cited, and kept visible so the answer remains auditable.")
    _render_evidence(view_model["evidence_rows"], backend_detail_rows(payload) if "top_evidence" in payload else [], payload, compact=True)

    render_step(4, "Answer + Trace", "The final response preserves route rationale and cited evidence ids.")
    _render_answer(payload["answer"])
    _render_trace(payload["reasoning_trace"])


def _render_route_header(payload: dict[str, object], view_model: dict[str, object]) -> None:
    rows = view_model.get("score_rows", [])
    margin = _score_margin(rows if isinstance(rows, list) else [])
    selected_backend = str(payload["selected_backend"])
    answer = payload.get("answer", {})
    support = _as_float(answer.get("support_score") if isinstance(answer, dict) else None)
    gold_route = view_model.get("gold_route") or "not benchmark"
    route_match = view_model.get("route_match")
    status = "n/a" if route_match is None else ("match" if route_match else "mismatch")

    cols = st.columns(4)
    with cols[0]:
        render_card("Selected backend", selected_backend.upper(), "Production route decision.")
        render_badges([route_badge(selected_backend)])
    with cols[1]:
        render_card("RAS margin", f"{margin:.3f}", "Gap between best and second-best route.")
    with cols[2]:
        render_card("Support score", f"{support:.3f}", "Evidence support reported by answerer.")
    with cols[3]:
        render_card("Benchmark route", str(gold_route).upper(), f"Route status: {status}.")


def _render_scores(rows: list[dict[str, object]]) -> None:
    df = pd.DataFrame(rows)
    if df.empty:
        render_info_card("No route scores are available for this run.", warning=True)
        return
    df["route"] = df["backend"].astype(str).str.upper()
    df["ras_score"] = pd.to_numeric(df["ras_score"], errors="coerce").fillna(0.0)
    chart_df = df[["route", "ras_score"]].set_index("route")
    st.bar_chart(chart_df, use_container_width=True)
    selected = next((row for row in rows if row.get("selected")), None)
    if selected:
        render_info_card(f"Chosen backend: {selected['backend']} because it has the lowest computed RAS score.")
    with st.expander("Route score table", expanded=False):
        st.dataframe(df, hide_index=True, use_container_width=True)


def _render_answer(answer: dict[str, object]) -> None:
    st.markdown("### Final Answer")
    render_card(
        "Answer",
        answer.get("final_answer", "No answer generated."),
        f"Answer type: {answer.get('answer_type', 'unknown')} | Rationale: {answer.get('route_rationale', 'not provided')}",
    )


def _render_evidence(
    evidence_rows: list[dict[str, object]],
    detail_rows: list[dict[str, object]],
    payload: dict[str, object],
    *,
    compact: bool = False,
) -> None:
    selected_backend = payload.get("selected_backend", "")
    if not evidence_rows:
        render_info_card("No evidence rows are available yet. Run a query or switch to benchmark mode.", warning=True)
        return
    top_rows = evidence_rows[:3] if compact else evidence_rows
    for row in top_rows:
        score = _format_score(row.get("score"))
        evidence_card(row.get("rank"), row.get("id"), score, row.get("type"), row.get("snippet"), selected_backend)
        if not compact:
            with st.expander(f"Metadata for evidence #{row.get('rank')}", expanded=False):
                st.json(row.get("metadata", {}))

    scores = [
        {"rank": row.get("rank"), "score": _as_float(row.get("score"))}
        for row in evidence_rows
        if row.get("score") is not None
    ]
    if scores:
        st.caption("Evidence score/rank view")
        st.bar_chart(pd.DataFrame(scores).set_index("rank"), use_container_width=True)

    if detail_rows and not compact:
        st.markdown("### Backend-Specific Evidence Metadata")
        st.caption("BM25, Dense, KG, and Hybrid expose different metadata; this table keeps that provenance visible.")
        st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)


def _render_trace(trace: list[dict[str, object]]) -> None:
    st.markdown("### Reasoning Trace")
    if not trace:
        render_info_card("No trace was generated for this run.", warning=True)
        return
    for index, step in enumerate(trace, start=1):
        title = str(step.get("step", f"trace step {index}"))
        with st.expander(f"{index}. {title}", expanded=index == 1):
            st.json(step)


def _render_raw(payload: dict[str, object], view_model: dict[str, object]) -> None:
    with st.expander("Raw demo payload", expanded=False):
        st.json({"gold_route": view_model.get("gold_route"), "gold_answer": view_model.get("gold_answer"), "payload": payload})


def _render_open_workspace(open_workspace: dict[str, object]) -> None:
    st.markdown("## Open Corpus Workspace")
    for warning in open_workspace.get("warnings", []):
        render_info_card(str(warning), warning=True)
    graph_count = int(open_workspace.get("query_local_graph", {}).get("triple_count", 0))
    index_status = open_workspace.get("index_status", {})
    source_types = open_workspace.get("source_types", {})

    cols = st.columns(4)
    with cols[0]:
        render_card("Source mode", open_workspace.get("source_mode", "unknown"), "Bounded runtime corpus.")
    with cols[1]:
        render_card("Documents", int(open_workspace.get("document_count", 0)), "Normalized local documents.")
    with cols[2]:
        render_card("Selected backend", str(open_workspace.get("selected_backend", "")).upper(), "Computed RAS route.")
        render_badges([route_badge(open_workspace.get("selected_backend", ""))])
    with cols[3]:
        render_card("Query-local graph", graph_count, "Triples extracted for this query.")

    st.markdown("### Runtime Corpus Metadata")
    cols = st.columns(3)
    with cols[0]:
        render_card("Index readiness", ", ".join(f"{k}: {v}" for k, v in index_status.items()), "Built in runtime scope.", compact=True)
    with cols[1]:
        render_card("Source types", ", ".join(f"{k}: {v}" for k, v in source_types.items()) or "unknown", "Provenance mix.", compact=True)
    with cols[2]:
        render_card("Graph readiness", "available" if graph_count else "not extracted", "Text evidence remains available.", compact=True)

    with st.expander("Runtime corpus paths and metadata", expanded=False):
        st.json(
            {
                "runtime_corpus": open_workspace.get("runtime_corpus"),
                "source_types": source_types,
                "index_status": index_status,
            }
        )

    st.markdown("### Route Comparison")
    st.dataframe(pd.DataFrame(open_workspace.get("route_comparison", [])), hide_index=True, use_container_width=True)
    st.markdown("### Routing Mode Comparison")
    st.dataframe(pd.DataFrame(open_workspace.get("routing_modes", [])), hide_index=True, use_container_width=True)


def _render_graph(open_workspace: dict[str, object]) -> None:
    st.markdown("## Query-Local Graph / Structured Path")
    graph = open_workspace.get("query_local_graph", {})
    if not graph or not graph.get("triple_count"):
        render_info_card("No query-local graph triples were extracted for this query. Text evidence remains available.")
        return
    render_card("Extracted triples", graph.get("triple_count", 0), "Rule-based query-local graph, exported for inspection.")
    triples = graph.get("triples", [])
    if triples:
        st.dataframe(pd.DataFrame(triples), hide_index=True, use_container_width=True)
    with st.expander("Graph artifact", expanded=False):
        st.json(graph)


def _render_router_comparison(open_workspace: dict[str, object] | None, payload: dict[str, object]) -> None:
    st.markdown("## Production vs Research Routing Modes")
    render_info_card(
        "Production uses computed_ras. Calibrated rescue, classifier_router, RAS_V3, RAS_V4, and optional LLM are research comparison layers."
    )
    if open_workspace:
        rows = open_workspace.get("routing_modes", [])
    else:
        rows = [
            {"mode": "computed_ras", "route": payload.get("selected_backend"), "status": "production default"},
            {"mode": "calibrated_rescue", "route": "analysis-only", "status": "available via calibration verifier"},
            {"mode": "classifier_router", "route": "analysis-only", "status": "available via router baseline artifacts"},
            {"mode": "ras_v3", "route": "analysis-only", "status": "not promoted"},
            {"mode": "ras_v4", "route": "analysis-only", "status": "not promoted; complements rescue"},
            {"mode": "optional_llm", "route": "optional", "status": "shown only if local endpoint is available"},
        ]
    cols = st.columns(3)
    for index, row in enumerate(rows):
        with cols[index % 3]:
            render_badges([mode_badge(row.get("mode", "unknown")), route_badge(row.get("route", "unknown"))])
            render_card(
                str(row.get("mode", "unknown")),
                str(row.get("route", "unknown")).upper(),
                str(row.get("status") or row.get("rationale") or row.get("confidence_or_margin") or ""),
                compact=True,
            )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_demo_overview() -> None:
    st.markdown("## Demo Overview")
    render_info_card("Select a preset in the sidebar, keep benchmark mode for the most reproducible path, then run PRISM.")
    cols = st.columns(4)
    status = _cached_json("data/final_release/known_results_summary.json")
    card_data = [
        ("Curated", _result_value(status, "curated", "answer_matches", "80/80"), "Restored end-to-end benchmark."),
        ("External mini", _result_value(status, "external_mini", "answer_accuracy", "1.000"), "32-example external check."),
        ("Production", "computed_ras", "Default route remains deterministic."),
        ("Research", "RAS_V4 + rescue", "Visible as overlays only."),
    ]
    for col, (title, value, caption) in zip(cols, card_data):
        with col:
            render_card(title, value, caption)

    st.markdown("### Demo Presets")
    df = pd.DataFrame(presets_payload())
    st.dataframe(
        df[["category", "title", "expected_route", "demo_mode", "badge", "presenter_note"]],
        hide_index=True,
        use_container_width=True,
    )


def _render_guided_demo() -> None:
    script = demo_script_payload()
    render_section_header(
        "Guided demo",
        "A compact walkthrough of PRISM's core ideas",
        "The sequence moves from deterministic production routing to evidence inspection, open-corpus scope, and research overlays.",
    )
    show_notes = st.checkbox("Presenter view", value=False, help="Show concise narration notes for live delivery.")
    cols = st.columns(3)
    with cols[0]:
        render_card("Production path", "computed_ras", "Default deterministic router.")
    with cols[1]:
        render_card("Research overlays", "clearly labeled", "Rescue, classifier, RAS_V3, RAS_V4, and optional LLM.")
    with cols[2]:
        render_card("Safe scope", "bounded corpora", "Benchmark, source-pack, or local corpus evidence.")

    st.markdown("### Demonstration Scenarios")
    for step in script.get("script_steps", []):
        with st.container(border=True):
            render_badges([badge(f"Step {step['step']}"), badge(step["mode"]), badge(step["preset"])])
            st.markdown(f"#### {step['title']}")
            st.caption("Focus: " + ", ".join(str(item) for item in step.get("show", [])))
            if show_notes:
                with st.expander("Presenter notes", expanded=False):
                    st.write(step["talk_track"])

    st.markdown("### Reliable Benchmark Sequence")
    render_info_card(str(script.get("fallback_note", "")))
    st.write("  →  ".join(str(item) for item in script.get("safe_fallback_sequence", [])))

    st.markdown("### Workspace Map")
    tab_rows = [
        {"tab": "Demo / Query", "purpose": "Run the production path and inspect query, route, evidence, answer, trace."},
        {"tab": "RAS Explainer", "purpose": "Explain computed RAS, RAS_V2, RAS_V3, RAS_V4, margins, and ambiguity flags."},
        {"tab": "Open Corpus", "purpose": "Show source-pack/local-corpus metadata and query-local graph readiness."},
        {"tab": "Compare Routers", "purpose": "Compare production computed_ras against research overlays."},
        {"tab": "Evidence / Graph", "purpose": "Inspect ranked evidence, metadata, and graph/path evidence."},
        {"tab": "Human Eval", "purpose": "Show real annotation and comparative human-eval highlights."},
        {"tab": "Results / Paper", "purpose": "Present central claim, release status, and caveats."},
    ]
    st.dataframe(pd.DataFrame(tab_rows), hide_index=True, use_container_width=True)


def _render_ras_explainer(query: str) -> None:
    render_section_header(
        "RAS explainer",
        "Representation Adequacy Score",
        "RAS estimates which representation can best support a query before answer generation: lexical text, dense semantics, graph structure, or a hybrid path.",
    )
    comparison = build_version_comparison()
    version_rows = comparison["versions"]

    cols = st.columns(4)
    with cols[0]:
        render_card("Production", "computed_ras", "Deterministic penalty table.")
    with cols[1]:
        render_card("Route adequacy", "RAS_V3", "Learned linear route model.")
    with cols[2]:
        render_card("Joint adequacy", "RAS_V4", "Route score plus evidence support.")
    with cols[3]:
        render_card("Rescue overlay", "calibrated", "Top-k evidence rescue for hard cases.")

    render_section_header(
        "Why routing matters",
        "Different questions need different evidence structures",
        "Exact identifiers favor BM25, conceptual paraphrases favor Dense retrieval, deductive claims favor KG evidence, and bridge/path questions often need Hybrid retrieval.",
    )
    _render_ras_family_diagram()

    render_section_header(
        "RAS family overview",
        "Production router and research variants",
        "The comparison keeps production behavior distinct from analysis-only variants while showing how the modeling assumptions evolve.",
    )
    st.dataframe(pd.DataFrame(version_rows), hide_index=True, use_container_width=True)
    chart_rows = pd.DataFrame(
        [
            {"version": row["name"], "uses evidence": int(bool(row["uses_evidence"])), "learned/tuned": int(bool(row["learned"]))}
            for row in version_rows
        ]
    ).set_index("version")
    st.bar_chart(chart_rows, use_container_width=True)
    st.caption("Binary indicators summarize whether a variant uses retrieved evidence diagnostics and whether it has learned or tuned weights.")

    render_section_header(
        "Mathematical layer",
        "Compact equations aligned with implementation",
        "Heuristic routers are shown as scoring rules; learned variants expose their linear scoring form.",
    )
    _render_notation_glossary()
    _render_ras_formula_panels()

    render_section_header(
        "Routing walkthrough",
        "From query features to evidence-backed answer",
        "The stepper shows the production routing flow without changing the underlying decision logic.",
    )
    story = _ras_story_payload(query)
    step_index = st.slider("Walkthrough step", 1, len(story), 1)
    step = story[step_index - 1]
    render_step(step_index, str(step["title"]), str(step["caption"]))
    if step["kind"] == "json":
        st.json(step["payload"])
    elif step["kind"] == "chart":
        st.bar_chart(pd.DataFrame(step["payload"]).set_index("route"), use_container_width=True)
    else:
        render_info_card(str(step["payload"]))

    render_section_header(
        "Query-level explanation",
        "Inspect the current sidebar query",
        "The panel shows the selected route, score margin, feature effects, and advisory ambiguity signal.",
    )
    _render_query_level_ras_inspection(query)

    render_section_header(
        "Sensitivity and robustness",
        "Where RAS variants agree, diverge, or become low margin",
        "These artifacts are descriptive analysis outputs; they do not alter production routing.",
    )
    sensitivity = _cached_json("data/eval/ras_sensitivity.json")
    if sensitivity:
        cols = st.columns(3)
        with cols[0]:
            render_card("Items analyzed", sensitivity.get("item_count", "n/a"), "Adversarial benchmark.")
        with cols[1]:
            summary = sensitivity.get("version_disagreement_summary", {})
            render_card("Version disagreements", summary.get("version_disagreement_count", "n/a") if isinstance(summary, dict) else "n/a", "RAS variants differ.")
        with cols[2]:
            render_card("Ambiguity flags", summary.get("advisory_ambiguity_count", "n/a") if isinstance(summary, dict) else "n/a", "Advisory only.")
    else:
        render_info_card("Sensitivity artifacts are unavailable. Rebuild the RAS explainer artifacts to refresh this section.", warning=True)
    _markdown_expander("data/eval/ras_confusion_summary.md", expanded=False)


def _render_ras_family_diagram() -> None:
    rows = [
        ("BM25", "lexical", "Exact identifiers, codes, and formal names."),
        ("Dense", "semantic", "Conceptual paraphrases and similarity."),
        ("KG", "deductive", "Class, property, and membership evidence."),
        ("Hybrid", "relational", "Bridge/path cases that combine text and structure."),
    ]
    cols = st.columns(4)
    for col, (route, cue, copy) in zip(cols, rows):
        with col:
            render_mini_card(route, copy, badge_html=route_badge(route.lower()) + badge(cue))


def _render_notation_glossary() -> None:
    with st.expander("Notation", expanded=False):
        cols = st.columns(2)
        left = [
            ("x", "query text"),
            ("r", "candidate route/backend in {BM25, Dense, KG, Hybrid}"),
            ("f_j(x)", "query feature or cue"),
            ("p_r(x)", "computed-RAS penalty for route r"),
        ]
        right = [
            ("E_r(x)", "top-k evidence retrieved by route r"),
            ("s_r(x)", "RAS_V3 route adequacy score"),
            ("z_r(x)", "RAS_V4 joint route/evidence score"),
            ("m", "margin between winner and runner-up"),
        ]
        for col, rows in zip(cols, [left, right]):
            with col:
                for symbol, meaning in rows:
                    render_status_line(f"{symbol}: {meaning}")


def _render_formula_panel(title: str, status: str, equations: list[str], where: list[str], interpretation: str) -> None:
    st.markdown(f"#### {title}")
    render_badges([badge(status)])
    for equation in equations:
        st.latex(equation)
    with st.expander("Terms", expanded=False):
        for row in where:
            st.markdown(f"- {row}")
    st.caption(interpretation)


def _render_ras_formula_panels() -> None:
    tabs = st.tabs(["computed_ras", "computed_ras_v2", "RAS_V3", "RAS_V4"])
    with tabs[0]:
        _render_formula_panel(
            "computed_ras",
            "production",
            [
                r"p_r(x)=1+\Delta_r^{lex}(x)+\Delta_r^{sem}(x)+\Delta_r^{ded}(x)+\Delta_r^{rel}(x)",
                r"\hat r=\arg\min_{r\in R}p_r(x)",
                r"\Delta_{bm25}^{lex}=-0.6,\quad \Delta_{dense}^{lex}=+0.2,\quad \Delta_{dense}^{sem}=-0.5",
                r"\Delta_{kg}^{ded}=-0.6,\quad \Delta_{hybrid}^{rel}=-0.7,\quad \Delta_{kg}^{rel}=-0.2",
            ],
            [
                "`p_r(x)` is an inadequacy penalty; lower is better.",
                "`lex`, `sem`, `ded`, and `rel` are parser cues for lexical, semantic, deductive, and relational questions.",
                "If no cue fires, the parser uses the semantic fallback implemented in `parse_query_features`.",
            ],
            "The production router selects the route with the lowest penalty table score.",
        )
    with tabs[1]:
        _render_formula_panel(
            "computed_ras_v2",
            "analysis-only",
            [
                r"\hat r_{v2}=g(\hat r_{ras},x,m,c)",
                r"""g(\cdot)=
\begin{cases}
hybrid & rel(x)\\
kg & ded(x)\land \neg strong\_id(x)\\
dense & id(x)\land sem\_amb(x)\land \neg strong\_id(x)\\
bm25 & strong\_id(x)\\
\hat r_{ras} & otherwise
\end{cases}""",
            ],
            [
                "`g` is a deterministic rule overlay, not a learned model.",
                "`m` is the computed-RAS margin and `c` is optional source/corpus context.",
                "The rules are intentionally narrow and remain research-only.",
            ],
            "RAS_V2 formalizes hard-case correction rules without replacing production computed RAS.",
        )
    with tabs[2]:
        _render_formula_panel(
            "RAS_V3",
            "analysis-only",
            [
                r"s_r(x)=b_r+\sum_j w_{rj}f_j(x)",
                r"\hat r_{v3}=\arg\max_{r\in R}s_r(x)",
            ],
            [
                "`f_j(x)` are interpretable query/source/context features.",
                "`w_{rj}` is the learned sparse linear weight for feature `j` and route `r`.",
                "Explanations report per-feature contributions to each route score.",
            ],
            "RAS_V3 turns route adequacy into a learned but inspectable linear route-scoring model.",
        )
    with tabs[3]:
        _render_formula_panel(
            "RAS_V4",
            "analysis-only",
            [
                r"z_r(x)=b+\sum_j\alpha_j q_j(x,r)+\sum_k\beta_k e_k(E_r(x),x)",
                r"\hat r_{v4}=\arg\max_{r\in R}z_r(x)",
                r"z_r=\underbrace{b+\sum_j\alpha_jq_j}_{route\ adequacy}+\underbrace{\sum_k\beta_ke_k}_{evidence\ adequacy}",
            ],
            [
                "`q_j` are route adequacy features.",
                "`e_k` are evidence adequacy diagnostics from the candidate route's top-k evidence.",
                "The decomposition separates route fit from expected answer support.",
            ],
            "RAS_V4 is the joint adequacy research model, but current results still keep it analysis-only.",
        )


def _render_query_level_ras_inspection(query: str) -> None:
    explanation = explain_query(query)
    flag = explanation["ambiguity_flag"]
    st.markdown("#### Why This Route?")
    render_badges([mode_badge("computed_ras"), route_badge(explanation["computed_ras"]["selected_backend"])])
    cols = st.columns(3)
    with cols[0]:
        render_card("Selected route", str(explanation["computed_ras"]["selected_backend"]).upper(), "Production computed RAS.")
    with cols[1]:
        render_card("Margin", f"{float(explanation['computed_ras']['margin']):.3f}", "Small margin means close alternatives.")
    with cols[2]:
        render_card("Ambiguity", "yes" if flag["is_ambiguous"] else "no", str(flag["message"]))

    score_rows = [{"route": key.upper(), "score": value} for key, value in explanation["computed_ras"]["scores"].items()]
    st.bar_chart(pd.DataFrame(score_rows).set_index("route"), use_container_width=True)
    with st.expander("Computed RAS feature effects", expanded=False):
        st.dataframe(pd.DataFrame(explanation["computed_ras"]["feature_effects"]), hide_index=True, use_container_width=True)
    with st.expander("RAS version votes and advisory flag", expanded=False):
        st.json({"route_votes": explanation["route_votes"], "ambiguity_flag": flag})
    v3 = explanation.get("ras_v3", {})
    if isinstance(v3, dict) and v3.get("top_selected_route_contributions"):
        st.markdown("#### RAS_V3 Feature Contributions")
        contrib_rows = pd.DataFrame(v3["top_selected_route_contributions"])
        st.bar_chart(contrib_rows.set_index("feature"), use_container_width=True)
    v4 = explanation.get("ras_v4", {})
    if isinstance(v4, dict):
        with st.expander("RAS_V4 availability / evidence adequacy note", expanded=False):
            st.json(v4)


def _ras_story_payload(query: str) -> list[dict[str, object]]:
    explanation = explain_query(query)
    computed = explanation["computed_ras"]
    return [
        {"title": "Query arrives", "caption": "The user asks a question over a bounded corpus.", "kind": "text", "payload": query},
        {"title": "Query features extracted", "caption": "Heuristic features detect lexical, semantic, deductive, and relational cues.", "kind": "json", "payload": computed["features"]},
        {
            "title": "Candidate route scores computed",
            "caption": "computed_ras applies the production penalty table. Lower score is better.",
            "kind": "chart",
            "payload": [{"route": key.upper(), "score": value} for key, value in computed["scores"].items()],
        },
        {
            "title": "Best route selected",
            "caption": "The minimum-penalty route becomes the production backend.",
            "kind": "text",
            "payload": f"Selected backend: {computed['selected_backend'].upper()} with margin {float(computed['margin']):.3f}.",
        },
        {
            "title": "Ambiguity checked",
            "caption": "This advisory flag never overrides production routing.",
            "kind": "json",
            "payload": explanation["ambiguity_flag"],
        },
        {
            "title": "Evidence and answer follow",
            "caption": "Retrieval, answer synthesis, and trace generation happen after route selection.",
            "kind": "text",
            "payload": "Run the query in `Demo / Query` to inspect evidence cards and the final trace.",
        },
    ]


def _render_open_corpus_guidance() -> None:
    st.markdown("## Open Corpus")
    render_info_card(
        "Open-corpus mode answers over bounded source packs, local folders, or URL-list corpora. "
        "It is not arbitrary web-scale QA, and runtime corpora remain separate from benchmark corpora."
    )
    packs = list_source_packs()
    cols = st.columns(3)
    with cols[0]:
        render_card("Built-in source packs", len(packs), ", ".join(packs))
    with cols[1]:
        render_card("Local demo folder", "available", "Safe fallback for live presentations.")
    with cols[2]:
        render_card("URL list mode", "optional", "Uses cache/fetch path and falls back gracefully.")
    st.markdown("### How to Use")
    st.write("Pick a mode in the sidebar, choose a preset query, then run PRISM. Runtime output lives under `data/runtime_corpora/`.")


def _render_research_mode_guidance() -> None:
    st.markdown("## Research Comparison Modes")
    rows = [
        ("computed_ras", "Production", "Default deterministic representation-aware router."),
        ("calibrated_rescue", "Research overlay", "Hard-case rescue comparison; not the default path."),
        ("classifier_router", "Research baseline", "Comparison router for evaluation artifacts."),
        ("ras_v3", "Analysis-only", "Interpretable route adequacy model; not promoted."),
        ("ras_v4", "Analysis-only", "Joint route/evidence adequacy model; not promoted."),
        ("optional_llm", "Optional experiment", "Shown only if a local endpoint is available."),
    ]
    cols = st.columns(3)
    for index, (mode, status, note) in enumerate(rows):
        with cols[index % 3]:
            render_badges([mode_badge(mode), badge(status)])
            render_card(mode, status, note, compact=True)


def _render_human_eval_summary() -> None:
    st.markdown("## Human Eval")
    standard = _cached_json("data/human_eval/human_eval_summary.json")
    comparative = _cached_json("data/human_eval/comparative_summary.json")
    ras_v4_human = _cached_json("data/human_eval/ras_v4_vs_human_summary.json")

    cols = st.columns(4)
    with cols[0]:
        render_card("Evaluators", standard.get("evaluator_count", comparative.get("evaluator_count", "n/a")), "Real annotation CSVs analyzed.")
    with cols[1]:
        render_card("Standard packet", standard.get("packet_size", "n/a"), "Trace and answer quality rubric.")
    with cols[2]:
        render_card("Comparative packet", comparative.get("packet_size", "n/a"), "Pairwise system preferences.")
    with cols[3]:
        render_card("RAS_V4 human link", ras_v4_human.get("status", "available" if ras_v4_human else "missing"), "Alignment stays report-facing.")

    dimension_means = standard.get("dimension_means", {})
    if isinstance(dimension_means, dict) and dimension_means:
        st.markdown("### Average Human Scores by Dimension")
        st.bar_chart(pd.DataFrame({"score": dimension_means}).sort_index(), use_container_width=True)
    else:
        render_info_card("Human-eval dimension means are unavailable or partial.", warning=True)

    pair_results = comparative.get("system_pair_results", {})
    if isinstance(pair_results, dict) and pair_results:
        st.markdown("### Comparative System-Pair Results")
        pair_rows = []
        for pair, row in pair_results.items():
            if isinstance(row, dict):
                preferences = row.get("overall_preference", {})
                if not isinstance(preferences, dict):
                    preferences = {}
                pair_rows.append(
                    {
                        "pair": pair,
                        "A wins": row.get("a_wins", preferences.get("A", 0)),
                        "B wins": row.get("b_wins", preferences.get("B", 0)),
                        "ties": row.get("ties", preferences.get("Tie", 0)),
                    }
                )
        if pair_rows:
            st.dataframe(pd.DataFrame(pair_rows), hide_index=True, use_container_width=True)

    for path in [
        "data/human_eval/human_eval_summary.md",
        "data/human_eval/comparative_summary.md",
        "data/human_eval/ras_v4_vs_human_summary.md",
    ]:
        _markdown_expander(path, expanded=False)


def _render_results_summary() -> None:
    st.markdown("## Results / Paper")
    results = _cached_json("data/final_release/known_results_summary.json")
    cols = st.columns(4)
    with cols[0]:
        render_card("Production router", results.get("production_router", "computed_ras"), "Final demo default.")
    with cols[1]:
        render_card("RAS_V4 status", "analysis-only", "Interpretable research method, not promoted.")
    with cols[2]:
        render_card("Open-corpus scope", "bounded", "Source-pack/local-corpus QA, not web-scale search.")
    with cols[3]:
        render_card("Release package", "generated", "data/final_release/")

    overview_rows = _benchmark_overview_rows(results)
    if overview_rows:
        st.markdown("### Benchmark Snapshot")
        df = pd.DataFrame(overview_rows)
        st.dataframe(df, hide_index=True, use_container_width=True)
        chart_rows = df.dropna(subset=["answer_accuracy"])
        if not chart_rows.empty:
            st.bar_chart(chart_rows.set_index("benchmark")["answer_accuracy"], use_container_width=True)

    _markdown_expander("data/final_release/central_claim_summary.md", expanded=True)
    _markdown_expander("data/eval/ras_v4_eval_summary.md", expanded=False)
    _markdown_expander("data/eval/report/prism_report_summary.md", expanded=False)


def _markdown_expander(path: str, *, expanded: bool) -> None:
    file_path = Path(path)
    if not file_path.exists():
        render_info_card(f"Missing optional artifact: {path}. Run the relevant verifier or release builder.", warning=True)
        return
    with st.expander(path, expanded=expanded):
        st.markdown(file_path.read_text(encoding="utf-8"))


def _benchmark_overview_rows(results: dict[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key in ["external_mini", "generalization_v2", "public_raw", "adversarial", "ras_v4_adversarial_test"]:
        value = results.get(key, {})
        if isinstance(value, dict):
            rows.append(
                {
                    "benchmark": key,
                    "route_accuracy": value.get("route_accuracy"),
                    "answer_accuracy": value.get("answer_accuracy"),
                    "evidence_hit_at_k": value.get("evidence_hit_at_k"),
                    "path": value.get("path"),
                }
            )
    return rows


def _result_value(results: dict[str, Any], section: str, field: str, fallback: object) -> object:
    value = results.get(section, {})
    if isinstance(value, dict):
        return value.get(field, fallback)
    return fallback


def _score_margin(rows: list[dict[str, object]]) -> float:
    scores = sorted(_as_float(row.get("ras_score")) for row in rows)
    if len(scores) < 2:
        return 0.0
    return scores[1] - scores[0]


def _as_float(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _format_score(value: object) -> str:
    try:
        return f"{float(value):.4f}"  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "n/a"


if __name__ == "__main__":
    main()
