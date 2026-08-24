"""Structured reconstruction that preserves the exact source representation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.equations.ast import ExprNode, NodeKind, parse_equation, serialize_node

__all__ = (
    "EquationReconstruction",
    "ReconstructionState",
    "reconstruct_equation",
)

_GREEK_LATEX = {
    "alpha": r"\alpha",
    "beta": r"\beta",
    "gamma": r"\gamma",
    "delta": r"\delta",
    "epsilon": r"\epsilon",
    "theta": r"\theta",
    "lambda": r"\lambda",
    "mu": r"\mu",
    "nu": r"\nu",
    "rho": r"\rho",
    "sigma": r"\sigma",
    "tau": r"\tau",
    "phi": r"\phi",
    "psi": r"\psi",
    "omega": r"\omega",
    "Delta": r"\Delta",
    "Sigma": r"\Sigma",
    "Omega": r"\Omega",
}

_GREEK_UNICODE = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "phi": "φ",
    "psi": "ψ",
    "omega": "ω",
    "Delta": "Δ",
    "Sigma": "Σ",
    "Omega": "Ω",
}


class ReconstructionState(Enum):
    RECONSTRUCTED = "RECONSTRUCTED"
    PARTIAL = "PARTIAL"
    EXTRACTION_UNAVAILABLE = "EXTRACTION_UNAVAILABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_PROVEN = "NOT_PROVEN"


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationReconstruction:
    source_equation_id: str
    source_representation: str
    normalized_representation: str
    hypothesized_greek: str | None
    latex: str | None
    mathml: str | None
    tree: ExprNode | None
    state: ReconstructionState
    reasons: tuple[str, ...]


def reconstruct_equation(source_equation_id: str, source_representation: str) -> EquationReconstruction:
    source = source_representation.strip()
    tree = parse_equation(source)
    if tree is None:
        return EquationReconstruction(
            source_equation_id=source_equation_id,
            source_representation=source,
            normalized_representation=source,
            hypothesized_greek=None,
            latex=None,
            mathml=None,
            tree=None,
            state=ReconstructionState.EXTRACTION_UNAVAILABLE,
            reasons=("parse failed; source representation retained",),
        )
    normalized = serialize_node(tree)
    greek = _hypothesized_greek(tree)
    latex = _to_latex(tree)
    mathml = _to_mathml(tree)
    changed = greek != normalized
    reasons: tuple[str, ...] = ("AST reconstructed from source text",)
    if changed:
        reasons = (
            *reasons,
            "Greek symbol form is hypothesized from ASCII names; source is authoritative",
        )
    return EquationReconstruction(
        source_equation_id=source_equation_id,
        source_representation=source,
        normalized_representation=normalized,
        hypothesized_greek=greek if changed else None,
        latex=latex,
        mathml=mathml,
        tree=tree,
        state=ReconstructionState.REVIEW_REQUIRED if changed else ReconstructionState.RECONSTRUCTED,
        reasons=reasons,
    )


def _hypothesized_greek(node: ExprNode) -> str:
    mapped = _map_symbols(node, _GREEK_UNICODE)
    return serialize_node(mapped)


def _map_symbols(node: ExprNode, mapping: dict[str, str]) -> ExprNode:
    value = node.value
    if node.kind is NodeKind.SYMBOL and value in mapping:
        value = mapping[value]
    return ExprNode(
        kind=node.kind,
        value=value,
        children=tuple(_map_symbols(child, mapping) for child in node.children),
    )


def _to_latex(node: ExprNode) -> str:
    if node.kind is NodeKind.SYMBOL:
        name = node.value or ""
        if "_" in name:
            head, tail = name.split("_", 1)
            head = _GREEK_LATEX.get(head, head)
            return f"{head}_{{{tail}}}"
        return _GREEK_LATEX.get(name, name)
    if node.kind is NodeKind.NUMBER:
        return node.value or ""
    if node.kind is NodeKind.NEG:
        return f"-{_to_latex(node.children[0])}"
    if node.kind is NodeKind.GROUP:
        return f"\\left({_to_latex(node.children[0])}\\right)"
    if node.kind is NodeKind.CALL:
        args = ", ".join(_to_latex(child) for child in node.children)
        return f"\\{node.value}({args})"
    if node.kind is NodeKind.EQ:
        return f"{_to_latex(node.children[0])} = {_to_latex(node.children[1])}"
    if node.kind is NodeKind.DIV:
        return f"\\frac{{{_to_latex(node.children[0])}}}{{{_to_latex(node.children[1])}}}"
    if node.kind is NodeKind.POW:
        return f"{{{_to_latex(node.children[0])}}}^{{{_to_latex(node.children[1])}}}"
    if node.kind is NodeKind.MUL:
        return " ".join(_to_latex(child) for child in node.children)
    op = " + " if node.kind is NodeKind.ADD else " - "
    return op.join(_to_latex(child) for child in node.children)


def _to_mathml(node: ExprNode) -> str:
    inner = _mathml_inner(node)
    return f"<math>{inner}</math>"


def _mathml_inner(node: ExprNode) -> str:
    if node.kind is NodeKind.SYMBOL:
        return f"<mi>{_xml(node.value or '')}</mi>"
    if node.kind is NodeKind.NUMBER:
        return f"<mn>{_xml(node.value or '')}</mn>"
    if node.kind is NodeKind.NEG:
        return f"<mrow><mo>-</mo>{_mathml_inner(node.children[0])}</mrow>"
    if node.kind is NodeKind.GROUP:
        return f"<mrow><mo>(</mo>{_mathml_inner(node.children[0])}<mo>)</mo></mrow>"
    if node.kind is NodeKind.CALL:
        args = "".join(_mathml_inner(child) for child in node.children)
        return f"<mrow><mi>{_xml(node.value or '')}</mi><mo>(</mo>{args}<mo>)</mo></mrow>"
    if node.kind is NodeKind.EQ:
        return (
            f"<mrow>{_mathml_inner(node.children[0])}<mo>=</mo>"
            f"{_mathml_inner(node.children[1])}</mrow>"
        )
    if node.kind is NodeKind.DIV:
        return (
            f"<mfrac>{_mathml_inner(node.children[0])}"
            f"{_mathml_inner(node.children[1])}</mfrac>"
        )
    if node.kind is NodeKind.POW:
        return (
            f"<msup>{_mathml_inner(node.children[0])}"
            f"{_mathml_inner(node.children[1])}</msup>"
        )
    op = {"ADD": "+", "SUB": "-", "MUL": "·"}[node.kind.name]
    body = f"<mo>{op}</mo>".join(_mathml_inner(child) for child in node.children)
    return f"<mrow>{body}</mrow>"


def _xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
