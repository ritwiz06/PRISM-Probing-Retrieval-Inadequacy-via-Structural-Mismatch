from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from prism.answering.generator import synthesize_answer
from prism.config import load_config
from prism.llm_experiments.llm_router import LLMRouter
from prism.open_corpus.build_source_pack import build_source_pack
from prism.open_corpus.load_urls import load_url_documents
from prism.open_corpus.normalize_documents import document_metadata_payload
from prism.open_corpus.query_local_graph import build_query_local_graph, export_query_local_graph
from prism.open_corpus.verify_open_corpus import _build_local_demo_docs, _runtime_retrievers
from prism.open_corpus.workspace import RUNTIME_ROOT, build_runtime_corpus_from_local
from prism.ras.compute_ras import route_query
from prism.ras.route_improvement import route_query_v2
from prism.router_baselines.rule_router import keyword_rule_route
from prism.utils import read_json, read_jsonl_documents, write_json, write_jsonl_documents


def build_open_workspace_view_model(
    query: str,
    *,
    source_mode: str = "source_pack",
    source_pack: str = "wikipedia",
    local_paths: list[str] | None = None,
    urls: list[str] | None = None,
    top_k: int | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    if source_mode == "local_demo":
        summary = _build_local_demo_docs()
    elif source_mode == "local_folder":
        if local_paths:
            summary = build_runtime_corpus_from_local(local_paths, name="ui_local_folder")
        else:
            summary = _build_local_demo_docs()
            warnings.append("No local folder was provided; using the bundled local demo folder.")
    elif source_mode == "url_list":
        summary, url_warnings = _build_url_runtime_corpus(urls or [])
        warnings.extend(url_warnings)
    else:
        summary = build_source_pack(source_pack)
    documents = read_jsonl_documents(Path(summary["documents_path"]))
    metadata_path = Path(str(summary.get("metadata_path", "")))
    runtime_metadata = read_json(metadata_path) if metadata_path.exists() else {}
    graph = build_query_local_graph(query, documents)
    graph_artifact = export_query_local_graph(graph, summary["output_dir"], "ui_latest")
    retrievers = _runtime_retrievers(documents, graph.triples)
    decision = route_query(query)
    selected_backend = decision.selected_backend
    limit = top_k or load_config().retrieval.default_top_k
    evidence = retrievers[selected_backend].retrieve(query, top_k=5 if selected_backend == "hybrid" else limit)
    answer = synthesize_answer(query, decision.features, decision.ras_scores, selected_backend, evidence)
    return {
        "query": query,
        "source_mode": source_mode,
        "source_pack": source_pack if source_mode == "source_pack" else None,
        "runtime_corpus": summary,
        "runtime_corpus_metadata": runtime_metadata,
        "warnings": warnings,
        "document_count": len(documents),
        "source_types": _source_types(runtime_metadata, documents),
        "index_status": {"bm25": "built_in_memory", "dense": "built_in_memory", "kg": "query_local_graph", "hybrid": "built_in_memory"},
        "parsed_features": asdict(decision.features),
        "ras_scores": decision.ras_scores,
        "selected_backend": selected_backend,
        "answer": asdict(answer),
        "top_evidence": [
            {
                "item_id": item.item_id,
                "score": item.score,
                "source_type": item.source_type,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in evidence
        ],
        "reasoning_trace": answer.reasoning_trace_steps,
        "query_local_graph": {
            "triple_count": len(graph.triples),
            "triples": [asdict(triple) for triple in graph.triples[:20]],
            "artifact": graph_artifact,
        },
        "route_comparison": compare_routes(query, retrievers),
        "routing_modes": compare_routing_modes(query),
    }


def compare_routes(query: str, retrievers: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for backend in ("bm25", "dense", "kg", "hybrid"):
        evidence = retrievers[backend].retrieve(query, top_k=3)
        rows.append(
            {
                "backend": backend,
                "top_evidence_id": evidence[0].item_id if evidence else "",
                "top_score": evidence[0].score if evidence else 0.0,
                "top_snippet": evidence[0].content[:180] if evidence else "",
                "evidence_count": len(evidence),
            }
        )
    return rows


def compare_routing_modes(query: str) -> list[dict[str, object]]:
    computed = route_query(query)
    v2 = route_query_v2(query)
    keyword = keyword_rule_route(query)
    llm_diag = LLMRouter().diagnostics()
    return [
        {"mode": "computed_ras", "route": computed.selected_backend, "confidence_or_margin": "", "rationale": "production minimum-RAS router"},
        {"mode": "computed_ras_v2", "route": v2.selected_backend, "confidence_or_margin": v2.margin, "rationale": v2.rationale},
        {"mode": "keyword_rule_router", "route": keyword.route, "confidence_or_margin": max(keyword.scores.values()), "rationale": keyword.rationale},
        {
            "mode": "llm_router",
            "route": "unavailable" if not llm_diag.get("available") else "available",
            "confidence_or_margin": "",
            "rationale": str(llm_diag.get("error") or "local LLM endpoint available"),
        },
    ]


def _build_url_runtime_corpus(urls: list[str]) -> tuple[dict[str, object], list[str]]:
    warnings: list[str] = []
    clean_urls = [url.strip() for url in urls if url.strip()]
    if not clean_urls:
        summary = _build_local_demo_docs()
        return summary, ["No URLs were provided; using the bundled local demo folder."]
    normalized, fetch_log = load_url_documents(clean_urls)
    if not normalized:
        summary = _build_local_demo_docs()
        return summary, ["No URL documents could be loaded from cache or network; using the bundled local demo folder."]
    output_dir = RUNTIME_ROOT / "ui_url_list"
    output_dir.mkdir(parents=True, exist_ok=True)
    documents_path = output_dir / "documents.jsonl"
    metadata_path = output_dir / "metadata.json"
    write_jsonl_documents(documents_path, [entry.document for entry in normalized])
    metadata = document_metadata_payload("ui_url_list", normalized)
    metadata.update(
        {
            "output_dir": str(output_dir),
            "documents_path": str(documents_path),
            "mode": "url_list",
            "fetch_log": fetch_log,
        }
    )
    write_json(metadata_path, metadata)
    skipped = [row for row in fetch_log if row.get("status") == "skipped"]
    if skipped:
        warnings.append(f"{len(skipped)} URL(s) were skipped; cached or successfully fetched URLs are still usable.")
    return {
        "name": "ui_url_list",
        "document_count": len(normalized),
        "output_dir": str(output_dir),
        "documents_path": str(documents_path),
        "metadata_path": str(metadata_path),
    }, warnings


def _source_types(metadata: object, documents: list[object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if isinstance(metadata, dict):
        for row in metadata.get("documents", []):
            if isinstance(row, dict):
                source_type = str(row.get("source_type") or "unknown")
                counts[source_type] = counts.get(source_type, 0) + 1
    if not counts:
        for document in documents:
            source_type = str(getattr(document, "source", "unknown")).split(":", 1)[0]
            counts[source_type] = counts.get(source_type, 0) + 1
    return counts
