"""Step 4 adversarial and contract-hardening tests for COMPAT-001→006."""

from __future__ import annotations

from pathlib import Path

import pytest

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphLifecycleState,
    GraphNode,
    GraphNodeIdentity,
    GraphQueryService,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.exceptions import GraphQueryError
from knowledge.graph.graph_manager import GraphManager
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.keyword_index import build_keyword_index_from_store
from knowledge.indexing.w7 import W7IndexBuilder, deterministic_reference_vector
from knowledge.ingestion.markdown_loader import load_markdown
from knowledge.ontology import OntologyRegistry, OntologyTerm
from knowledge.ontology.exceptions import DuplicateOntologyTermError
from knowledge.ontology.ontology_manager import OntologyManager
from knowledge.pipelines.knowledge_pipeline import run_knowledge_pipeline
from knowledge.search import SearchFilter, SearchQuery
from knowledge.search.contracts import RetrievalMode
from knowledge.search.hybrid_search import HybridSearch
from knowledge.search.keyword_search import KeywordSearch
from knowledge.search.semantic_search import SemanticSearch


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _build_w7_stack(*labels: str):
    entities = tuple(
        CandidateEntityExtraction(
            extraction_id=f"ENT-{index}",
            document_id="DOC-001",
            extracted_label=label,
            entity_kind=ExtractedEntityKind.QUANTITY,
            canonical_entity_type=CanonicalEntityType.QUANTITY,
            provenance=_provenance(),
        )
        for index, label in enumerate(labels, start=1)
    )
    store = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=entities),
    ).store
    bundle = W7IndexBuilder().build(store)
    graph_query = GraphQueryService(store)
    return store, bundle, graph_query


def test_all_compat_surfaces_importable() -> None:
    """All six compatibility surfaces must expose their public legacy symbols."""

    from knowledge.compat import COMPATIBILITY_LAYER
    from knowledge.graph.graph_manager import GraphManager
    from knowledge.indexing.graph_index import GraphIndex
    from knowledge.indexing.keyword_index import KeywordIndex
    from knowledge.indexing.semantic_index import SemanticIndex
    from knowledge.ingestion.docx_loader import load_docx
    from knowledge.ingestion.html_loader import load_html
    from knowledge.ingestion.markdown_loader import load_markdown
    from knowledge.ingestion.pdf_loader import load_pdf
    from knowledge.ontology.ontology_manager import OntologyManager
    from knowledge.pipelines.knowledge_pipeline import run_knowledge_pipeline
    from knowledge.search.graph_search import GraphSearch
    from knowledge.search.hybrid_search import HybridSearch
    from knowledge.search.keyword_search import KeywordSearch
    from knowledge.search.search_engine import SearchEngine
    from knowledge.search.semantic_search import SemanticSearch

    assert COMPATIBILITY_LAYER is True
    for symbol in (
        load_pdf,
        load_docx,
        load_html,
        load_markdown,
        KeywordSearch,
        SemanticSearch,
        HybridSearch,
        GraphSearch,
        SearchEngine,
        KeywordIndex,
        SemanticIndex,
        GraphIndex,
        GraphManager,
        OntologyManager,
        run_knowledge_pipeline,
    ):
        assert symbol is not None


def test_load_markdown_deterministic_source_ids(tmp_path: Path) -> None:
    """COMPAT-001 must derive stable source/artifact IDs from path when omitted."""

    path = tmp_path / "unicode-α.md"
    path.write_text("# Título\n\nContenido\n", encoding="utf-8")

    first = load_markdown(path)
    second = load_markdown(path)

    assert first.request.artifact.source_id == second.request.artifact.source_id
    assert first.request.artifact.artifact_id == second.request.artifact.artifact_id
    assert first.request.artifact.content_hash == second.request.artifact.content_hash


def test_load_markdown_rejects_directory(tmp_path: Path) -> None:
    """COMPAT-001 must reject non-file paths."""

    with pytest.raises(FileNotFoundError, match="not a file"):
        load_markdown(tmp_path)


def test_keyword_search_facade_rejects_stale_index() -> None:
    """COMPAT-002 must propagate IndexStaleError when the bound store mutates."""

    store, bundle, _ = _build_w7_stack("Chamber Pressure")
    facade = KeywordSearch.from_lexical_index(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
        store=store,
    )

    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(node_id="ENT-NEW", node_type="Quantity"),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": "DOC-001",
                "canonical_name": "New",
            },
        ),
    )

    with pytest.raises(IndexStaleError):
        facade.search(SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL))


def test_semantic_search_facade_rejects_wrong_vector_dimension() -> None:
    """COMPAT-002 must surface vector dimension validation errors."""

    store, bundle, _ = _build_w7_stack("Chamber Pressure")
    facade = SemanticSearch.from_vector_index(
        bundle.vector_index,
        source_digest=bundle.source_digest,
        store=store,
    )

    with pytest.raises(IndexValidationError, match="dimension"):
        facade.search(
            SearchQuery(text="chamber", mode=RetrievalMode.SEMANTIC),
            query_vector=(1.0, 2.0),
        )


def test_hybrid_search_facade_is_deterministic() -> None:
    """COMPAT-002 must return identical ranked results for identical queries."""

    store, bundle, graph_query = _build_w7_stack("Chamber Pressure", "LOX")
    facade = HybridSearch.from_w7_bundle(bundle, graph_query, store)
    query = SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID)

    first = facade.search(query)
    second = facade.search(query)

    assert [result.target_id for result in first.results] == [
        result.target_id for result in second.results
    ]
    assert [result.score for result in first.results] == [
        result.score for result in second.results
    ]


def test_keyword_search_facade_respects_lifecycle_filter() -> None:
    """COMPAT-002 must honor lifecycle filters without promoting entities."""

    _, bundle, _ = _build_w7_stack("Chamber Pressure")
    facade = KeywordSearch.from_lexical_index(
        bundle.lexical_index,
        source_digest=bundle.source_digest,
    )
    page = facade.search(
        SearchQuery(
            text="chamber pressure",
            mode=RetrievalMode.LEXICAL,
            filters=SearchFilter(lifecycle_state="APPROVED"),
        ),
    )

    assert page.total_count == 0


def test_build_keyword_index_from_store_is_deterministic() -> None:
    """COMPAT-003 must build identical lexical lookups from the same store."""

    store, _, _ = _build_w7_stack("Chamber Pressure")
    first = build_keyword_index_from_store(store)
    second = build_keyword_index_from_store(store)

    assert first.lookup(("chamber",)) == second.lookup(("chamber",))


def test_graph_manager_store_requires_construct() -> None:
    """COMPAT-004 must reject store access before construction."""

    manager = GraphManager()

    with pytest.raises(GraphQueryError, match="no constructed graph"):
        _ = manager.store


def test_ontology_manager_rejects_duplicate_term_registration() -> None:
    """COMPAT-005 must propagate duplicate term errors from OntologyRegistry."""

    manager = OntologyManager()
    term = OntologyTerm(
        term_id="term-qty-pressure",
        canonical_name="Pressure",
        entity_type=CanonicalEntityType.QUANTITY,
    )
    manager.register_term(term)

    with pytest.raises(DuplicateOntologyTermError):
        manager.register_term(term)


def test_pipeline_does_not_promote_lifecycle_state() -> None:
    """COMPAT-006 must leave graph entities in CANDIDATE lifecycle state."""

    artifacts = run_knowledge_pipeline(
        "# Minimal\n\nNo explicit entities.\n",
        request_id="step4-lifecycle",
    )
    nodes = artifacts.store.snapshot().nodes

    assert nodes
    assert all(
        node.properties["lifecycle_state"] == GraphLifecycleState.CANDIDATE.value
        for node in nodes
    )


def test_pipeline_preserves_provider_invoked_false() -> None:
    """COMPAT-006 must preserve controlled local RAG trust boundary."""

    artifacts = run_knowledge_pipeline(
        "# Minimal\n\nProvider boundary check.\n",
        request_id="step4-provider",
    )

    assert artifacts.rag_result.provider_invoked is False
