"""Lite end-to-end acceptance: candidate extract → approve → query → provenance."""

from __future__ import annotations

from knowledge.extraction.correlation_extractor import extract_correlations
from knowledge.interface.engineering_query import EngineeringQueryService, QueryConstraints
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.correlation import Correlation
from knowledge.repositories.correlation_repository import CorrelationRepository
from knowledge.repositories.design_rule_repository import DesignRuleRepository
from knowledge.repositories.equation_repository import EquationRepository


def test_candidate_cannot_be_queried_until_approved() -> None:
    text = "The Bartz correlation is used for regenerative cooling."
    candidates = extract_correlations(text, document_id="DOC-SP-8087", reference_id="REF-SP-8087")
    assert candidates
    repo = CorrelationRepository()
    repo.create(candidates[0])

    service = EngineeringQueryService(
        equations=EquationRepository(),
        correlations=repo,
        design_rules=DesignRuleRepository(),
    )
    assert service.find_correlation("Bartz") == ()

    approved = Correlation(
        correlation_id="CORR-BARTZ-001",
        name="Bartz",
        equation="h = f(Re, Pr, geometry)",
        variables=("h", "Re", "Pr"),
        dimensionless_groups=("Re", "Pr"),
        provenance=ProvenanceTrace(
            source_reference_id="REF-SP-8087",
            document_id="DOC-SP-8087",
            page=12,
        ),
        lifecycle=KnowledgeLifecycle.APPROVED,
        validation_status="APPROVED",
        reynolds_range=(1e4, 1e6),
    )
    repo.create(approved)
    hits = service.find_correlation("Bartz", QueryConstraints(require_approved=True))
    assert hits[0].provenance.source_reference_id == "REF-SP-8087"
    assert hits[0].lifecycle is KnowledgeLifecycle.APPROVED
