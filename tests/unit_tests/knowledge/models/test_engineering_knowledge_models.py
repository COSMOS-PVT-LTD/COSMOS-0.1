"""Tests for canonical engineering knowledge models."""

from __future__ import annotations

import pytest

from knowledge.models.assumption import Assumption
from knowledge.models.boundary_condition import BoundaryCondition
from knowledge.models.correlation import Correlation
from knowledge.models.design_rule import DesignRule
from knowledge.models.dimension_check import check_dimensional_consistency
from knowledge.models.empirical_relation import EmpiricalRelation
from knowledge.models.engineering_relation import EngineeringRelationKind
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, UncertaintyRecord, VerificationRecord
from knowledge.models.physical_law import PhysicalLaw
from knowledge.models.property import PropertyDefinition, PropertyValue


def _prov() -> ProvenanceTrace:
    return ProvenanceTrace(source_reference_id="REF-NASA-SP-8087", document_id="DOC-SP-8087", page=42)


def test_physical_law_requires_formulation() -> None:
    with pytest.raises(ValueError):
        PhysicalLaw(
            law_id="LAW-001",
            name="Newton",
            description="x",
            mathematical_formulation=" ",
            variables=(),
            units=(),
            assumptions=(),
            domain="DYNAMICS",
            applicability="point mass",
            provenance=_prov(),
        )


def test_physical_law_as_relation() -> None:
    law = PhysicalLaw(
        law_id="LAW-N2",
        name="Newton's Second Law",
        description="Force equals mass times acceleration.",
        mathematical_formulation="F = m a",
        variables=("F", "m", "a"),
        units=("N", "kg", "m/s^2"),
        assumptions=("point mass",),
        domain="DYNAMICS",
        applicability="inertial frames",
        provenance=_prov(),
        lifecycle=KnowledgeLifecycle.CANDIDATE,
    )
    assert law.as_relation().kind is EngineeringRelationKind.PHYSICAL_LAW


def test_correlation_requires_provenance_and_ordered_range() -> None:
    with pytest.raises(ValueError):
        Correlation(
            correlation_id="CORR-BARTZ",
            name="Bartz",
            equation="h = ...",
            variables=("h",),
            dimensionless_groups=("Re", "Pr"),
            reynolds_range=(1e6, 1e3),
            provenance=_prov(),
        )


def test_approved_assumption_requires_approver() -> None:
    with pytest.raises(ValueError):
        Assumption(
            assumption_id="ASM-001",
            statement="Coolant is single-phase.",
            category="thermal",
            affected_entity_ids=("CORR-BARTZ",),
            provenance=_prov(),
            justification="NASA SP-8087",
            applicability="specified P/T range",
            confidence=0.8,
            lifecycle=KnowledgeLifecycle.APPROVED,
        )


def test_property_value_approved_requires_validity() -> None:
    with pytest.raises(ValueError):
        PropertyValue(
            value_id="PV-001",
            property_id="density",
            material_id="MAT-GRCOP",
            numeric_value=8900.0,
            unit="kg/m3",
            provenance=_prov(),
            lifecycle=KnowledgeLifecycle.APPROVED,
        )


def test_reynolds_dimensional_consistency() -> None:
    # rho: M L^-3, V: L T^-1, D: L, mu: M L^-1 T^-1, Re: 1
    result = check_dimensional_consistency(
        "Re = rho*V*D/mu",
        {
            "Re": (0, 0, 0, 0, 0, 0, 0),
            "rho": (-3, 1, 0, 0, 0, 0, 0),
            "V": (1, 0, -1, 0, 0, 0, 0),
            "D": (1, 0, 0, 0, 0, 0, 0),
            "mu": (-1, 1, -1, 0, 0, 0, 0),
        },
    )
    assert result.passed is True


def test_empirical_relation_is_not_a_correlation() -> None:
    relation = EmpiricalRelation(
        relation_id="EMP-001",
        name="Injector discharge fit",
        equation="Cd = a + b*Re",
        variables=("Cd", "Re"),
        domain="INJECTOR",
        data_basis="hot-fire series H-12",
        provenance=_prov(),
    )
    assert relation.as_relation().kind is EngineeringRelationKind.EMPIRICAL_RELATION


def test_design_rule_and_boundary_condition() -> None:
    rule = DesignRule(
        rule_id="RULE-SF",
        statement="minimum safety factor",
        formula="SF >= 1.5",
        parameters=("SF",),
        applicability="chamber wall",
        authority="internal standard",
        severity="HIGH",
        provenance=_prov(),
    )
    assert rule.as_relation().kind is EngineeringRelationKind.DESIGN_RULE
    bc = BoundaryCondition(
        boundary_condition_id="BC-TW",
        name="Wall temperature",
        quantity="temperature",
        value_expression="800",
        unit="K",
        geometry_location="chamber wall",
        applicable_solver="thermal",
        applicable_physics="heat_transfer",
        provenance=_prov(),
    )
    assert bc.quantity == "temperature"


def test_property_definition() -> None:
    definition = PropertyDefinition(
        property_id="PROP-K",
        name="thermal conductivity",
        symbol="k",
        dimension="M L T^-3 Θ^-1",
        unit="W/m/K",
        description="Fourier conductivity",
    )
    assert definition.symbol == "k"
