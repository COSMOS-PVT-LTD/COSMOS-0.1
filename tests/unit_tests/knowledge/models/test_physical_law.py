"""PhysicalLaw model tests."""

from __future__ import annotations

from knowledge.models.engineering_relation import EngineeringRelationKind
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.physical_law import PhysicalLaw


def test_physical_law_as_relation() -> None:
    law = PhysicalLaw(
        law_id="LAW-MASS",
        name="Conservation of Mass",
        description="Continuum mass balance",
        mathematical_formulation="d/dt ∫ rho dV + ∫ rho V·n dA = 0",
        variables=("rho", "V"),
        units=("kg/m^3", "m/s"),
        assumptions=("continuum",),
        domain="FLUID_MECHANICS",
        applicability="continuum",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        lifecycle=KnowledgeLifecycle.CANDIDATE,
        validation_status="APPROVED",
    )
    assert law.as_relation().kind is EngineeringRelationKind.PHYSICAL_LAW
    assert law.provenance.source_reference_id == "REF-1"
