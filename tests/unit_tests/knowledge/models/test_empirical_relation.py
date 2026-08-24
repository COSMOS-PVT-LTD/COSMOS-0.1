"""EmpiricalRelation is a sibling of Correlation."""

from __future__ import annotations

from knowledge.models.empirical_relation import EmpiricalRelation
from knowledge.models.engineering_relation import EngineeringRelationKind
from knowledge.models.lifecycle import ProvenanceTrace


def test_empirical_relation_is_not_a_correlation() -> None:
    relation = EmpiricalRelation(
        relation_id="EMP-1",
        name="Injector discharge fit",
        equation="Cd = a + b*Re",
        variables=("Cd", "Re"),
        domain="INJECTOR",
        data_basis="hot-fire series",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
    )
    assert relation.as_relation().kind is EngineeringRelationKind.EMPIRICAL_RELATION
