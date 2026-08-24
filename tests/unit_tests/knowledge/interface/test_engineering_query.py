"""Engineering query interface tests — approved outranks candidates."""

from __future__ import annotations

from knowledge.models.correlation import Correlation
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.interface.engineering_query import EngineeringQueryService, QueryConstraints
from knowledge.repositories.correlation_repository import CorrelationRepository
from knowledge.repositories.design_rule_repository import DesignRuleRepository
from knowledge.repositories.equation_repository import EquationRepository


def test_query_hides_unapproved_correlations_by_default() -> None:
    repo = CorrelationRepository()
    repo.create(
        Correlation(
            correlation_id="CORR-CAND",
            name="Bartz candidate",
            equation="h = ...",
            variables=(),
            dimensionless_groups=(),
            provenance=ProvenanceTrace(source_reference_id="R", document_id="D"),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
        ),
    )
    repo.create(
        Correlation(
            correlation_id="CORR-APPR",
            name="Bartz",
            equation="h = f(Re,Pr)",
            variables=("h",),
            dimensionless_groups=("Re", "Pr"),
            provenance=ProvenanceTrace(source_reference_id="R", document_id="D"),
            lifecycle=KnowledgeLifecycle.APPROVED,
        ),
    )
    service = EngineeringQueryService(
        equations=EquationRepository(),
        correlations=repo,
        design_rules=DesignRuleRepository(),
    )
    approved = service.find_correlation("Bartz")
    assert [item.correlation_id for item in approved] == ["CORR-APPR"]
    all_hits = service.find_correlation("Bartz", QueryConstraints(require_approved=False))
    assert len(all_hits) == 2


def test_find_helpers_are_empty_without_optional_stores() -> None:
    service = EngineeringQueryService(
        equations=EquationRepository(),
        correlations=CorrelationRepository(),
        design_rules=DesignRuleRepository(),
    )
    assert service.find_material("LOX") == ()
    assert service.find_property("density") == ()
    assert service.find_boundary_condition("wall") == ()
    assert service.find_failure_mode("creep") == ()
    assert service.find_experiment("hot-fire") == ()
    assert service.find_simulation("cfd") == ()
    assert service.find_source("NASA") == ()
