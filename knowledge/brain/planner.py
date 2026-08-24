"""Query planner for knowledge-brain retrieval. Does not invent answers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from knowledge.foundation.query_classification import QueryKind, classify_query

__all__ = ("PlannedQueryKind", "QueryPlan", "QueryPlanner")


class PlannedQueryKind(Enum):
    DOCUMENT_QUERY = "DOCUMENT_QUERY"
    SOURCE_QUERY = "SOURCE_QUERY"
    EQUATION_QUERY = "EQUATION_QUERY"
    VARIABLE_QUERY = "VARIABLE_QUERY"
    MATERIAL_QUERY = "MATERIAL_QUERY"
    CORRELATION_QUERY = "CORRELATION_QUERY"
    GRAPH_QUERY = "GRAPH_QUERY"
    COMPARISON_QUERY = "COMPARISON_QUERY"
    ENGINEERING_QUERY = "ENGINEERING_QUERY"
    DESIGN_QUERY = "DESIGN_QUERY"
    CALCULATION_QUERY = "CALCULATION_QUERY"


@dataclass(frozen=True, slots=True, kw_only=True)
class QueryPlan:
    text: str
    kind: PlannedQueryKind
    foundation_kind: QueryKind
    channels: tuple[str, ...]
    route_to_solver: bool
    notes: tuple[str, ...]


_SOURCE = re.compile(r"\b(document|source|pdf|this file|this note)\b", re.IGNORECASE)
_COMPARE = re.compile(r"\b(compare|difference|versus|vs\.?)\b", re.IGNORECASE)
_GRAPH = re.compile(r"\b(related|relationship|connected|graph)\b", re.IGNORECASE)
_CORR = re.compile(r"\b(correlation|bartz|nusselt|gnielinski|dittus)\b", re.IGNORECASE)
_DESIGN = re.compile(r"\b(design rule|should we|applicable|chamber|injector|nozzle)\b", re.IGNORECASE)
_CALC = re.compile(r"\b(calculate|run the calculation|compute|solve)\b", re.IGNORECASE)
_MATERIAL = re.compile(r"\b(material|grcop|inconel|lox|methane|ch4)\b", re.IGNORECASE)


class QueryPlanner:
    def plan(self, text: str) -> QueryPlan:
        cleaned = text.strip()
        foundation = classify_query(cleaned)
        notes: list[str] = []
        if _CALC.search(cleaned):
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.CALCULATION_QUERY,
                foundation_kind=foundation,
                channels=("physics_gateway", "approved_equations"),
                route_to_solver=True,
                notes=("Deterministic solvers require authorized approved inputs. Chat does not compute.",),
            )
        if _COMPARE.search(cleaned):
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.COMPARISON_QUERY,
                foundation_kind=foundation,
                channels=("documents", "keywords", "equations"),
                route_to_solver=False,
                notes=("Compare only retrieved evidence. Do not invent missing sources.",),
            )
        if _SOURCE.search(cleaned):
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.DOCUMENT_QUERY,
                foundation_kind=foundation,
                channels=("documents", "keywords"),
                route_to_solver=False,
                notes=tuple(notes),
            )
        if foundation is QueryKind.EQUATION or _CORR.search(cleaned):
            kind = PlannedQueryKind.CORRELATION_QUERY if _CORR.search(cleaned) else PlannedQueryKind.EQUATION_QUERY
            return QueryPlan(
                text=cleaned,
                kind=kind,
                foundation_kind=foundation,
                channels=("equations", "keywords", "variables", "documents"),
                route_to_solver=False,
                notes=tuple(notes),
            )
        if foundation is QueryKind.VARIABLE:
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.VARIABLE_QUERY,
                foundation_kind=foundation,
                channels=("variables", "equations"),
                route_to_solver=False,
                notes=tuple(notes),
            )
        if foundation is QueryKind.MATERIAL or _MATERIAL.search(cleaned):
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.MATERIAL_QUERY,
                foundation_kind=foundation,
                channels=("keywords", "documents"),
                route_to_solver=False,
                notes=tuple(notes),
            )
        if _GRAPH.search(cleaned):
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.GRAPH_QUERY,
                foundation_kind=foundation,
                channels=("graph", "keywords"),
                route_to_solver=False,
                notes=tuple(notes),
            )
        if _DESIGN.search(cleaned):
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.DESIGN_QUERY,
                foundation_kind=foundation,
                channels=("keywords", "equations", "documents"),
                route_to_solver=False,
                notes=("Applicability must come from retrieved evidence.",),
            )
        if foundation is QueryKind.CITATION:
            return QueryPlan(
                text=cleaned,
                kind=PlannedQueryKind.SOURCE_QUERY,
                foundation_kind=foundation,
                channels=("citations", "documents"),
                route_to_solver=False,
                notes=tuple(notes),
            )
        return QueryPlan(
            text=cleaned,
            kind=PlannedQueryKind.ENGINEERING_QUERY,
            foundation_kind=foundation,
            channels=("keywords", "equations", "documents", "graph"),
            route_to_solver=False,
            notes=tuple(notes),
        )
