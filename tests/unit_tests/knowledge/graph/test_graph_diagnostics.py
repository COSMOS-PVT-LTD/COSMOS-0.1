"""Step 6 graph integrity diagnostics tests."""

from __future__ import annotations

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph import GraphConstructionBatch, GraphConstructor, ProvenanceReference
from knowledge.graph.diagnostics import analyze_graph_integrity
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology import OntologyRegistry


def _entity(label: str, extraction_id: str = "ENT-1") -> CandidateEntityExtraction:
    return CandidateEntityExtraction(
        extraction_id=extraction_id,
        document_id="DOC-001",
        extracted_label=label,
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(document_id="DOC-001", page=1),
        ),
    )


def test_analyze_graph_integrity_flags_orphan_nodes() -> None:
    """Diagnostics must report nodes without incident relationships."""

    store = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(
            entity_extractions=(
                _entity("Chamber Pressure", "ENT-1"),
                _entity("LOX", "ENT-2"),
            ),
        ),
    ).store

    report = analyze_graph_integrity(store)

    assert report.orphan_count >= 1
    assert any(finding.code == "orphan_node" for finding in report.findings)


def test_analyze_graph_integrity_is_deterministic() -> None:
    """Graph diagnostics must be deterministic for identical stores."""

    store = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(_entity("Chamber Pressure"),)),
    ).store

    first = analyze_graph_integrity(store)
    second = analyze_graph_integrity(store)

    assert first.report_digest == second.report_digest
    assert first.to_mapping() == second.to_mapping()
