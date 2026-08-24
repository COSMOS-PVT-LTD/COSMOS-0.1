"""Typed engineering-graph views over the concept graph — not a second graph store."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.concept_graph import ConceptEdge, ConceptGraph
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship

__all__ = ("TypedGraphView", "typed_views")


@dataclass(frozen=True, slots=True, kw_only=True)
class TypedGraphView:
    name: str
    edges: tuple[ConceptEdge, ...]

    def related(self, entity_id: str) -> tuple[str, ...]:
        return tuple(edge.target_id for edge in self.edges if edge.source_id == entity_id)


def typed_views(graph: ConceptGraph) -> dict[str, TypedGraphView]:
    """Project the concept graph into the required engineering graph types."""

    edges = tuple(graph._edges)
    return {
        "engineering": TypedGraphView(name="engineering", edges=edges),
        "equation": _view("equation", edges, prefixes=("EQ-", "LAW-", "CORR-")),
        "variable": _view("variable", edges, prefixes=("VAR-",), relationships=(EngineeringRelationship.USES,)),
        "dependency": _view(
            "dependency",
            edges,
            relationships=(EngineeringRelationship.DEPENDS_ON, EngineeringRelationship.REQUIRES),
        ),
        "citation": _view(
            "citation",
            edges,
            prefixes=("DOC-", "REF-"),
            relationships=(EngineeringRelationship.DERIVED_FROM, EngineeringRelationship.SUPPORTS),
        ),
        "concept": TypedGraphView(name="concept", edges=edges),
        "material_property": _view("material_property", edges, prefixes=("MAT-", "PROP-", "PV-")),
        "component": _view("component", edges, prefixes=("COMP-",)),
        "design_rule": _view("design_rule", edges, prefixes=("RULE-",)),
        "failure": _view("failure", edges, prefixes=("FM-",)),
        "experiment": _view("experiment", edges, prefixes=("EXP-",)),
        "simulation": _view("simulation", edges, prefixes=("SIM-",)),
    }


def _view(
    name: str,
    edges: tuple[ConceptEdge, ...],
    *,
    prefixes: tuple[str, ...] = (),
    relationships: tuple[EngineeringRelationship, ...] = (),
) -> TypedGraphView:
    selected: list[ConceptEdge] = []
    for edge in edges:
        if relationships and edge.relationship not in relationships:
            continue
        if prefixes and not (
            edge.source_id.startswith(prefixes) or edge.target_id.startswith(prefixes)
        ):
            continue
        selected.append(edge)
    return TypedGraphView(name=name, edges=tuple(selected))
