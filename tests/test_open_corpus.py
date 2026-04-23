from __future__ import annotations

from pathlib import Path

from prism.open_corpus.build_source_pack import build_source_pack
from prism.open_corpus.load_local_docs import load_local_documents
from prism.open_corpus.normalize_documents import normalize_raw_document
from prism.open_corpus.query_local_graph import build_query_local_graph
from prism.open_corpus.view_model import compare_routing_modes
from prism.ras.route_improvement import route_query_v2
from prism.schemas import Document


def test_open_corpus_document_normalization() -> None:
    normalized = normalize_raw_document(
        text="<h1>RFC-7231</h1><p>HTTP semantics and content.</p>",
        title="RFC-7231",
        source_type="unit",
        provenance="inline",
        doc_id="unit_rfc_7231",
    )
    assert normalized.document.doc_id == "unit_rfc_7231"
    assert "HTTP semantics" in normalized.document.text
    assert normalized.metadata["source_type"] == "unit"


def test_local_folder_loader_structure(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("# Note\nA bat is a mammal.", encoding="utf-8")
    rows = load_local_documents([tmp_path])
    assert len(rows) == 1
    assert rows[0].document.title == "Note"


def test_source_pack_build_structure(tmp_path: Path) -> None:
    payload = build_source_pack("wikipedia", output_root=tmp_path)
    assert payload["document_count"] >= 1
    assert Path(payload["documents_path"]).exists()
    assert Path(payload["metadata_path"]).exists()


def test_query_local_graph_structure() -> None:
    documents = [
        Document(
            doc_id="doc_bat",
            title="Bat",
            text="A bat is a mammal. A mammal is a vertebrate. Bat connects to vertebrate through mammal.",
            source="unit",
        )
    ]
    graph = build_query_local_graph("What bridge connects bat and vertebrate?", documents)
    assert graph.triples
    assert graph.metadata["backend_type"] == "query_local_graph"


def test_ras_v2_output_structure() -> None:
    decision = route_query_v2("Which concept feels like RFC-7231 but is about worry?")
    assert decision.selected_backend in {"bm25", "dense", "kg", "hybrid"}
    assert decision.original_backend in {"bm25", "dense", "kg", "hybrid"}
    assert "identifier_heavy" in decision.signals


def test_open_workspace_routing_modes_shape() -> None:
    rows = compare_routing_modes("RFC-7231")
    modes = {row["mode"] for row in rows}
    assert "computed_ras" in modes
    assert "computed_ras_v2" in modes
