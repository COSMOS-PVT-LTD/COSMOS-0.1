"""Seeded knowledge foundation is queryable through the controlled interface."""

from __future__ import annotations

from knowledge.foundation import KnowledgeFoundationService
from knowledge.interface.engineering_query import QueryConstraints
from knowledge.models.lifecycle import KnowledgeLifecycle


def test_seed_corpus_answers_engineering_queries() -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    query = service.query_service()

    bartz = query.find_correlation("Bartz")
    assert bartz and bartz[0].lifecycle is KnowledgeLifecycle.APPROVED
    assert bartz[0].provenance.source_reference_id == "REF-NASA-SP-8087"

    assert query.find_physical_law("Reynolds", QueryConstraints(require_approved=True))
    assert query.find_material("GRCop-42")
    assert query.find_property("density", QueryConstraints(material="MAT-WATER"))
    assert query.find_design_rule("wall temperature")
    assert query.find_boundary_condition("heat flux")
    assert query.find_failure_mode("burn-through")
    assert query.find_experiment("regenerative")
    assert query.find_simulation("cfd")
    assert service.graph_integrity_passed() is True


def test_physics_gateway_returns_only_approved() -> None:
    gateway = KnowledgeFoundationService.with_seed_corpus().physics()
    correlation = gateway.get_approved_correlation("Bartz", reynolds_number=5.0e4)
    assert correlation.correlation_id == "CORR-BARTZ"
    law = gateway.get_approved_law("First Law")
    assert "Thermodynamics" in law.name


def test_search_hides_unapproved_empirical_fit() -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    result = service.search("injector discharge")
    assert all(hit.entity_id != "EMP-INJECTOR-CD-FIT" for hit in result.hits)
    bartz = service.search("Bartz regenerative cooling")
    assert bartz.hits
    assert bartz.hits[0].lifecycle is KnowledgeLifecycle.APPROVED
    assert bartz.provenance_ids
    answer = service.answer("Bartz")
    assert answer.confidence >= 0.8
    assert answer.supporting_document_ids
