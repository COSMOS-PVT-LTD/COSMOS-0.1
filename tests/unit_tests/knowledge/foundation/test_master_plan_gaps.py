"""Coverage for remaining master-plan capabilities."""

from __future__ import annotations

from knowledge.extraction.constant_extractor import extract_constant_candidates
from knowledge.extraction.variable_extractor import extract_variable_candidates
from knowledge.foundation import KnowledgeFoundationService
from knowledge.foundation.versioning import supersede_entity
from knowledge.graph.concept_graph import ConceptEdge, ConceptGraph
from knowledge.graph.integrity import validate_concept_graph
from knowledge.graph.typed_views import typed_views
from knowledge.models.correlation import Correlation
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship, relationship_spec
from knowledge.repositories.correlation_repository import CorrelationRepository


def test_find_source_returns_approved_references() -> None:
    query = KnowledgeFoundationService.with_seed_corpus().query_service()
    hits = query.find_source("NASA SP-8087")
    assert any(item.source_id == "REF-NASA-SP-8087" for item in hits)
    assert all(item.status == "APPROVED" for item in hits)


def test_variable_and_constant_extractors_stay_candidate() -> None:
    variables = extract_variable_candidates(
        "Re = rho * V * D / mu",
        document_id="DOC-1",
        reference_id="REF-1",
    )
    assert {item.symbol for item in variables} >= {"Re", "rho", "V", "D", "mu"}
    assert all(item.lifecycle is KnowledgeLifecycle.CANDIDATE for item in variables)
    constants = extract_constant_candidates(
        "Use g0 for specific impulse.",
        document_id="DOC-1",
        reference_id="REF-1",
    )
    assert constants[0].symbol == "g0"
    assert constants[0].lifecycle is KnowledgeLifecycle.CANDIDATE


def test_relationship_specs_cover_vocabulary() -> None:
    spec = relationship_spec(EngineeringRelationship.MITIGATES)
    assert "failure" in spec.target_kinds
    assert spec.cardinality


def test_typed_graph_views_project_seed_graph() -> None:
    views = typed_views(KnowledgeFoundationService.with_seed_corpus().graph)
    assert "equation" in views
    assert "failure" in views
    assert views["design_rule"].related("RULE-TWALL-MAX")


def test_integrity_detects_illegal_cycles() -> None:
    graph = ConceptGraph()
    graph.add(ConceptEdge(source_id="A", target_id="B", relationship=EngineeringRelationship.PART_OF))
    graph.add(ConceptEdge(source_id="B", target_id="A", relationship=EngineeringRelationship.PART_OF))
    report = validate_concept_graph(graph, frozenset({"A", "B"}))
    assert report.passed is False
    assert report.illegal_cycles


def test_supersede_retains_history() -> None:
    repo = CorrelationRepository()
    provenance = ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1")
    first = Correlation(
        correlation_id="CORR-X",
        name="v1",
        equation="Nu = 1",
        variables=("Nu",),
        dimensionless_groups=("Nu",),
        provenance=provenance,
        lifecycle=KnowledgeLifecycle.APPROVED,
    )
    second = Correlation(
        correlation_id="CORR-X",
        name="v2",
        equation="Nu = 2",
        variables=("Nu",),
        dimensionless_groups=("Nu",),
        provenance=provenance,
        lifecycle=KnowledgeLifecycle.APPROVED,
    )
    repo.create(first)
    record = supersede_entity(repo, "CORR-X", second, author="reviewer", reason="update", entity_version="2.0.0")
    assert record.version.supersedes_id == "CORR-X"
    assert len(repo.history("CORR-X")) >= 2


def test_reasoning_answer_exposes_limitations_and_sources() -> None:
    answer = KnowledgeFoundationService.with_seed_corpus().answer("Bartz")
    assert answer.limitations
    assert answer.validation_state == "APPROVED"
    assert answer.supporting_entities
    assert answer.source_references


def test_snapshot_includes_full_correlation_records(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = KnowledgeFoundationService.with_seed_corpus()
    path = tmp_path / "full.json"
    service.persist(path)
    loaded = service.load_snapshot(path)
    records = loaded["correlation_records"]
    assert isinstance(records, list)
    assert any(item["correlation_id"] == "CORR-BARTZ" for item in records)  # type: ignore[index]
