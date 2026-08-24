"""Equation AST reconstruction — source text is preserved."""

from __future__ import annotations

from knowledge.equations.ast import NodeKind, parse_equation, serialize_node
from knowledge.equations.equivalence import EquationRelation, classify_equation_relation
from knowledge.equations.reconstruction import ReconstructionState, reconstruct_equation


def test_parses_reynolds_and_ocr_spacing_as_equivalent() -> None:
    native = parse_equation("Re = rho * V * D / mu")
    ocr = parse_equation("Re =rho* V* D/ mu")
    assert native is not None and ocr is not None
    assert native.kind is NodeKind.EQ
    assert classify_equation_relation("Re = rho * V * D / mu", "Re =rho* V* D/ mu") is EquationRelation.EQUIVALENT
    reconstructed = reconstruct_equation("eq-1", "Re =rho* V* D/ mu")
    assert reconstructed.source_representation == "Re =rho* V* D/ mu"
    assert reconstructed.normalized_representation == serialize_node(ocr)
    assert reconstructed.latex is not None and "frac" in reconstructed.latex
    assert reconstructed.hypothesized_greek is not None
    assert reconstructed.state is ReconstructionState.REVIEW_REQUIRED


def test_nested_parentheses_and_power() -> None:
    tree = parse_equation("Re = (rho * V * D) / mu")
    assert tree is not None
    powered = parse_equation("a = b ** 2")
    assert powered is not None
    assert powered.children[1].kind is NodeKind.POW


def test_malformed_equation_is_not_invented() -> None:
    assert parse_equation("this has an = but not") is None
    reconstructed = reconstruct_equation("eq-bad", "not an identity")
    assert reconstructed.tree is None
    assert reconstructed.state.value == "EXTRACTION_UNAVAILABLE"
    assert reconstructed.source_representation == "not an identity"


def test_contradictory_and_incomparable_relations() -> None:
    assert (
        classify_equation_relation("Re = rho * V * D / mu", "Re = rho * V * D * mu")
        is EquationRelation.CONTRADICTORY
    )
    assert classify_equation_relation("Re = rho * V * D / mu", "Nu = h * L / k") is EquationRelation.NOT_COMPARABLE
    assert (
        classify_equation_relation(
            "Re = rho * V * D / mu",
            "Re = rho * V * D / mu",
            left_applicability="internal flow",
            right_applicability="external flow",
        )
        is EquationRelation.DIFFERENT_APPLICABILITY
    )
