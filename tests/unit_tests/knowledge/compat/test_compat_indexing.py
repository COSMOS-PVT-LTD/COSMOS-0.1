"""COMPAT-003 — frozen indexing facade tests."""

from __future__ import annotations

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing.graph_index import GraphIndex, build_graph_index_from_store
from knowledge.indexing.keyword_index import KeywordIndex, build_keyword_index_from_store
from knowledge.indexing.semantic_index import SemanticIndex, build_semantic_index_from_store
from knowledge.indexing.lexical import InMemoryLexicalIndex
from knowledge.indexing.semantic import InMemorySemanticIndex
from knowledge.indexing.w7.graph_index import InMemoryGraphIndex
from knowledge.ontology import OntologyRegistry


def _build_store(label: str = "Chamber Pressure"):
    entity = CandidateEntityExtraction(
        extraction_id="ENT-1",
        document_id="DOC-001",
        extracted_label=label,
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id="DOC-001", page=1),
        ),
    )
    return GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(entity,)),
    ).store


def test_keyword_index_alias_is_canonical_lexical_index() -> None:
    """KeywordIndex must alias InMemoryLexicalIndex."""

    assert KeywordIndex is InMemoryLexicalIndex


def test_semantic_index_alias_is_canonical_semantic_index() -> None:
    """SemanticIndex must alias InMemorySemanticIndex."""

    assert SemanticIndex is InMemorySemanticIndex


def test_graph_index_alias_is_canonical_w7_graph_index() -> None:
    """GraphIndex must alias InMemoryGraphIndex."""

    assert GraphIndex is InMemoryGraphIndex


def test_build_keyword_index_from_store_matches_canonical_builder() -> None:
    """build_keyword_index_from_store must produce a queryable lexical index."""

    store = _build_store()
    index = build_keyword_index_from_store(store)

    assert len(index.lookup(("chamber",))) >= 1


def test_build_semantic_index_from_store_matches_canonical_builder() -> None:
    """build_semantic_index_from_store must produce a semantic index."""

    store = _build_store()
    index = build_semantic_index_from_store(store)

    assert len(index.entries()) >= 1


def test_build_graph_index_from_store_matches_canonical_builder() -> None:
    """build_graph_index_from_store must produce a graph index."""

    store = _build_store()
    index = build_graph_index_from_store(store)

    assert len(index.adjacency()) >= 1
