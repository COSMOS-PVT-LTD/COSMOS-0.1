"""Unit tests for knowledge.graph construction pipeline."""

from __future__ import annotations

import pytest

from knowledge.extraction import (
    CandidateEntityExtraction,
    CandidateRelationshipExtraction,
    ExtractedEntityKind,
    ExtractionConfidence,
)
from knowledge.extraction.equation import CandidateEquationExtraction
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphLifecycleState,
    ProvenanceReference,
    GraphConstructionError,
    GraphValidationError,
    graph_node_id_for_extraction,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology import OntologyAlias, OntologyRegistry, OntologyTerm


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=2),
    )


def _sample_batch() -> GraphConstructionBatch:
    entity = CandidateEntityExtraction(
        extraction_id="ENT-001",
        document_id="DOC-001",
        extracted_label="Pc",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=_provenance(),
    )
    equation = CandidateEquationExtraction(
        extraction_id="EQ-001",
        document_id="DOC-001",
        raw_representation="P = F / A",
        provenance=_provenance(),
        confidence_band=ExtractionConfidence.MEDIUM,
        confidence_score=0.5,
    )
    relationship = CandidateRelationshipExtraction(
        relationship_id="REL-001",
        document_id="DOC-001",
        relationship_type="references",
        source_extraction_id="ENT-001",
        target_extraction_id="EQ-001",
        provenance=_provenance(),
    )

    return GraphConstructionBatch(
        entity_extractions=(entity,),
        equation_extractions=(equation,),
        relationship_extractions=(relationship,),
    )


def test_graph_constructor_builds_deterministic_graph() -> None:
    """Construction must produce stable nodes, relationships, and snapshot."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-pc",
            canonical_name="Chamber Pressure",
            entity_type=CanonicalEntityType.QUANTITY,
            aliases=(
                OntologyAlias(
                    alias="Pc",
                    canonical_term_id="term-pc",
                ),
            ),
        ),
    )

    constructor = GraphConstructor(registry)
    first = constructor.construct(_sample_batch(), snapshot_sequence=1)
    second = constructor.construct(_sample_batch(), snapshot_sequence=1)

    assert (
        first.snapshot.identity.content_digest
        == second.snapshot.identity.content_digest
    )
    assert len(first.entity_records) == 2
    assert len(first.relationship_records) == 1
    assert first.entity_records[0].node.properties["canonical_name"] == (
        "Chamber Pressure"
    )


def test_graph_constructor_preserves_candidate_lifecycle() -> None:
    """Constructed graph nodes must remain in candidate lifecycle states."""

    constructor = GraphConstructor(OntologyRegistry())
    result = constructor.construct(_sample_batch())

    for record in result.entity_records:
        assert record.node.properties["lifecycle_state"] in {
            GraphLifecycleState.EXTRACTED.value,
            GraphLifecycleState.CANDIDATE.value,
        }


def test_graph_constructor_is_independent_of_candidate_order() -> None:
    """Input tuple order must not affect constructed graph identity."""

    batch = _sample_batch()
    reversed_batch = GraphConstructionBatch(
        entity_extractions=tuple(reversed(batch.entity_extractions)),
        equation_extractions=tuple(reversed(batch.equation_extractions)),
        relationship_extractions=tuple(
            reversed(batch.relationship_extractions),
        ),
    )

    constructor = GraphConstructor(OntologyRegistry())
    forward = constructor.construct(batch, snapshot_sequence=1)
    backward = constructor.construct(reversed_batch, snapshot_sequence=1)

    assert (
        forward.snapshot.identity.content_digest
        == backward.snapshot.identity.content_digest
    )


def test_graph_node_id_for_extraction_strips_whitespace() -> None:
    """Node identifiers must normalize extraction identifiers deterministically."""

    assert graph_node_id_for_extraction("  ENT-001  ") == "ENT-001"


def test_graph_node_id_for_extraction_rejects_blank_values() -> None:
    """Blank extraction identifiers must be rejected."""

    with pytest.raises(GraphValidationError):
        graph_node_id_for_extraction("   ")


def test_graph_constructor_rejects_approved_entity_extraction() -> None:
    """Approved candidates must not enter the construction pipeline."""

    entity = CandidateEntityExtraction(
        extraction_id="ENT-001",
        document_id="DOC-001",
        extracted_label="Pc",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=_provenance(),
        lifecycle_state=GraphLifecycleState.APPROVED,
    )

    batch = GraphConstructionBatch(entity_extractions=(entity,))

    with pytest.raises(GraphConstructionError):
        GraphConstructor(OntologyRegistry()).construct(batch)


def test_graph_constructor_rejects_relationship_with_missing_endpoints() -> None:
    """Relationships must reference nodes present in the same construction batch."""

    relationship = CandidateRelationshipExtraction(
        relationship_id="REL-001",
        document_id="DOC-001",
        relationship_type="references",
        source_extraction_id="ENT-001",
        target_extraction_id="EQ-001",
        provenance=_provenance(),
    )

    batch = GraphConstructionBatch(
        relationship_extractions=(relationship,),
    )

    with pytest.raises(GraphConstructionError):
        GraphConstructor(OntologyRegistry()).construct(batch)


def test_graph_constructor_preserves_relationship_provenance() -> None:
    """Relationship provenance must survive graph construction."""

    provenance = _provenance()
    batch = GraphConstructionBatch(
        entity_extractions=(
            CandidateEntityExtraction(
                extraction_id="ENT-001",
                document_id="DOC-001",
                extracted_label="Pc",
                entity_kind=ExtractedEntityKind.QUANTITY,
                canonical_entity_type=CanonicalEntityType.QUANTITY,
                provenance=provenance,
            ),
        ),
        equation_extractions=(
            CandidateEquationExtraction(
                extraction_id="EQ-001",
                document_id="DOC-001",
                raw_representation="P = F / A",
                provenance=provenance,
            ),
        ),
        relationship_extractions=(
            CandidateRelationshipExtraction(
                relationship_id="REL-001",
                document_id="DOC-001",
                relationship_type="references",
                source_extraction_id="ENT-001",
                target_extraction_id="EQ-001",
                provenance=provenance,
            ),
        ),
    )

    result = GraphConstructor(OntologyRegistry()).construct(batch)

    assert result.relationship_records[0].provenance == provenance


def test_graph_constructor_uses_extraction_id_as_node_identity() -> None:
    """Graph node identifiers must remain stable one-to-one with extraction IDs."""

    result = GraphConstructor(OntologyRegistry()).construct(_sample_batch())

    node_ids = {record.node.node_id for record in result.entity_records}

    assert node_ids == {"ENT-001", "EQ-001"}
