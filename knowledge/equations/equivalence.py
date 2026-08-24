"""Equation relation classification. Never silently picks a winner."""

from __future__ import annotations

from enum import Enum

from knowledge.equations.ast import ExprNode, NodeKind, parse_equation

__all__ = ("EquationRelation", "classify_equation_relation")


class EquationRelation(Enum):
    EQUIVALENT = "EQUIVALENT"
    CONDITIONALLY_EQUIVALENT = "CONDITIONALLY_EQUIVALENT"
    DIFFERENT_APPLICABILITY = "DIFFERENT_APPLICABILITY"
    NUMERICALLY_DIFFERENT = "NUMERICALLY_DIFFERENT"
    CONTRADICTORY = "CONTRADICTORY"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    NOT_PROVEN = "NOT_PROVEN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


def classify_equation_relation(
    left_text: str,
    right_text: str,
    *,
    left_applicability: str | None = None,
    right_applicability: str | None = None,
) -> EquationRelation:
    left = parse_equation(left_text)
    right = parse_equation(right_text)
    if left is None or right is None:
        if left_text.strip() == right_text.strip():
            return EquationRelation.EQUIVALENT
        return EquationRelation.NOT_PROVEN
    if left.kind is not NodeKind.EQ or right.kind is not NodeKind.EQ:
        return EquationRelation.NOT_PROVEN
    left_lhs = _canonical(left.children[0])
    right_lhs = _canonical(right.children[0])
    if left_lhs != right_lhs:
        return EquationRelation.NOT_COMPARABLE
    left_rhs = _canonical(left.children[1])
    right_rhs = _canonical(right.children[1])
    if left_rhs == right_rhs:
        if _applicability_differs(left_applicability, right_applicability):
            return EquationRelation.DIFFERENT_APPLICABILITY
        return EquationRelation.EQUIVALENT
    return EquationRelation.CONTRADICTORY


def _applicability_differs(left: str | None, right: str | None) -> bool:
    left_norm = (left or "").strip().lower()
    right_norm = (right or "").strip().lower()
    return bool(left_norm and right_norm and left_norm != right_norm)


def _canonical(node: ExprNode) -> tuple[object, ...]:
    if node.kind is NodeKind.GROUP and node.children:
        return _canonical(node.children[0])
    if node.kind in {NodeKind.MUL, NodeKind.ADD} and len(node.children) == 2:
        flat = _flatten(node, node.kind)
        keyed = sorted((_canonical(child) for child in flat), key=repr)
        return (node.kind.value, tuple(keyed))
    children = tuple(_canonical(child) for child in node.children)
    return (node.kind.value, node.value, children)


def _flatten(node: ExprNode, kind: NodeKind) -> tuple[ExprNode, ...]:
    items: list[ExprNode] = []
    for child in node.children:
        actual = child.children[0] if child.kind is NodeKind.GROUP and child.children else child
        if actual.kind is kind:
            items.extend(_flatten(actual, kind))
        else:
            items.append(actual)
    return tuple(items)
