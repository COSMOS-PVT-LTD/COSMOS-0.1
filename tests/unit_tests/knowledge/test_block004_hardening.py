"""KG-BLOCK-004 engineering review hardening tests."""

from __future__ import annotations

import pytest

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
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
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing import (
    IndexEntry,
    IndexValidationError,
    InMemoryLexicalIndex,
    KnowledgeIndexBuilder,
    build_lexical_index_from_store,
)
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.ontology import OntologyRegistry
from knowledge.reasoning import EvidenceRanker, ProvenanceAwareReasoner
from knowledge.search import (
    KnowledgeSearchEngine,
    RetrievalMode,
    SearchQuery,
)


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _build_store_with_entities(
    *labels: str,
):
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

    return GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=entities),
    ).store


def test_lexical_index_rejects_duplicate_entry_ids() -> None:
    """Duplicate entry identities must fail deterministically."""

    entry = IndexEntry(
        entry_id="lex:ENT-1",
        target_id="ENT-1",
        target_type="Quantity",
        terms=("pressure",),
    )

    with pytest.raises(IndexValidationError, match="Duplicate lexical entry_id"):
        InMemoryLexicalIndex(
            index_id="lexical-test",
            source_digest="digest-a",
            entries=(entry, entry),
        )


def test_index_build_is_independent_of_construction_batch_order() -> None:
    """Index digests must not depend on extraction batch ordering."""

    def _entities(
        *pairs: tuple[str, str],
    ) -> tuple[CandidateEntityExtraction, ...]:
        return tuple(
            CandidateEntityExtraction(
                extraction_id=extraction_id,
                document_id="DOC-001",
                extracted_label=label,
                entity_kind=ExtractedEntityKind.QUANTITY,
                canonical_entity_type=CanonicalEntityType.QUANTITY,
                provenance=_provenance(),
            )
            for extraction_id, label in pairs
        )

    store_a = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(
            entity_extractions=_entities(
                ("ENT-A", "Alpha Pressure"),
                ("ENT-B", "Beta Pressure"),
            ),
        ),
    ).store
    store_b = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(
            entity_extractions=_entities(
                ("ENT-B", "Beta Pressure"),
                ("ENT-A", "Alpha Pressure"),
            ),
        ),
    ).store

    digest_a = build_lexical_index_from_store(store_a).metadata().source_digest
    digest_b = build_lexical_index_from_store(store_b).metadata().source_digest

    assert digest_a == digest_b


def test_empty_graph_produces_empty_index() -> None:
    """Empty authoritative graphs must produce empty derivative indexes."""

    from knowledge.graph.memory_store import InMemoryGraphStore

    bundle = KnowledgeIndexBuilder().build(InMemoryGraphStore())

    assert bundle.lexical_index.statistics().entry_count == 0
    assert bundle.semantic_index.statistics().entry_count == 0


def test_search_rejects_stale_indexes_after_graph_mutation() -> None:
    """Search must not serve stale indexes after graph mutation."""

    store = _build_store_with_entities("Chamber Pressure")
    bundle = KnowledgeIndexBuilder().build(store)
    engine = KnowledgeSearchEngine(
        bundle,
        GraphQueryService(store),
        store,
    )

    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="ENT-NEW",
                node_type="Quantity",
            ),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": "DOC-001",
                "canonical_name": "New Entity",
            },
        ),
    )

    with pytest.raises(IndexStaleError):
        engine.search(SearchQuery(text="chamber", mode=RetrievalMode.LEXICAL))


def test_structured_search_does_not_return_irrelevant_nodes() -> None:
    """Structured retrieval must not return unrelated graph nodes."""

    store = _build_store_with_entities("Chamber Pressure")
    bundle = KnowledgeIndexBuilder().build(store)
    engine = KnowledgeSearchEngine(
        bundle,
        GraphQueryService(store),
        store,
    )

    page = engine.search(
        SearchQuery(text="nonexistent-term-xyz", mode=RetrievalMode.STRUCTURED),
    )

    assert page.total_count == 0
    assert page.results == ()


def test_hybrid_search_tie_breaks_by_target_id() -> None:
    """Equal hybrid scores must tie-break deterministically by target_id."""

    store = _build_store_with_entities("Shared Term", "Shared Term")
    bundle = KnowledgeIndexBuilder().build(store)
    engine = KnowledgeSearchEngine(
        bundle,
        GraphQueryService(store),
        store,
    )

    query = SearchQuery(text="shared", mode=RetrievalMode.HYBRID)
    first = engine.search(query)
    second = engine.search(query)

    assert [item.target_id for item in first.results] == [
        item.target_id for item in second.results
    ]
    assert [item.target_id for item in first.results] == sorted(
        item.target_id for item in first.results
    )


def test_reasoner_preserves_conflicting_evidence() -> None:
    """Confirmed conflicts must be surfaced without silent resolution."""

    store = _build_store_with_entities("Conflict Quantity")
    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="ENT-CONFLICT",
                node_type="Quantity",
            ),
            properties={
                "lifecycle_state": GraphLifecycleState.CANDIDATE.value,
                "document_id": "DOC-002",
                "canonical_name": "Conflict Quantity",
                "extracted_label": "Conflict Quantity",
                "conflict_visibility": "CONFIRMED_CONFLICT",
            },
        ),
    )

    graph_query = GraphQueryService(store)
    bundle = KnowledgeIndexBuilder().build(store)
    engine = KnowledgeSearchEngine(bundle, graph_query, store)
    page = engine.search(
        SearchQuery(text="conflict", mode=RetrievalMode.LEXICAL),
    )
    evidence = EvidenceRanker(graph_query).assemble(page.results)

    assessment = ProvenanceAwareReasoner().assess(evidence)

    assert "ENT-CONFLICT" in assessment.conflict_target_ids
    assert "ENT-CONFLICT" not in assessment.candidate_target_ids


def test_approved_evidence_is_classified_as_verified() -> None:
    """Approved lifecycle evidence must be classified as verified."""

    store = _build_store_with_entities("Verified Quantity")
    store.add_node(
        GraphNode(
            identity=GraphNodeIdentity(
                node_id="ENT-APPROVED",
                node_type="Quantity",
            ),
            properties={
                "lifecycle_state": GraphLifecycleState.APPROVED.value,
                "document_id": "DOC-001",
                "canonical_name": "Verified Quantity",
                "extracted_label": "Verified Quantity",
            },
        ),
    )

    graph_query = GraphQueryService(store)
    bundle = KnowledgeIndexBuilder().build(store)
    engine = KnowledgeSearchEngine(bundle, graph_query, store)
    page = engine.search(
        SearchQuery(text="verified", mode=RetrievalMode.LEXICAL),
    )
    evidence = EvidenceRanker(graph_query).assemble(page.results)

    assert evidence.has_verified_results
    assessment = ProvenanceAwareReasoner().assess(evidence)

    assert assessment.supported_target_ids == ("ENT-APPROVED",)
