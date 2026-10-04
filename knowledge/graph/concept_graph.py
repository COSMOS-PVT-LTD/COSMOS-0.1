"""Concept graph — explicit engineering relationships."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.ontology.engineering_vocabulary import EngineeringRelationship

__all__ = ("ConceptEdge", "ConceptGraph")


@dataclass(frozen=True, slots=True, kw_only=True)
class ConceptEdge:
    source_id: str
    target_id: str
    relationship: EngineeringRelationship


class ConceptGraph:
    def __init__(self) -> None:
        self._edges: list[ConceptEdge] = []

    def add(self, edge: ConceptEdge) -> None:
        key = (edge.source_id, edge.target_id, edge.relationship)
        if any(
            (existing.source_id, existing.target_id, existing.relationship) == key
            for existing in self._edges
        ):
            return
        self._edges.append(edge)

    def remove_incident(self, node_id: str) -> int:
        before = len(self._edges)
        self._edges = [
            edge
            for edge in self._edges
            if edge.source_id != node_id and edge.target_id != node_id
        ]
        return before - len(self._edges)

    def neighbors(self, source_id: str) -> tuple[ConceptEdge, ...]:
        return tuple(edge for edge in self._edges if edge.source_id == source_id)

    def related(self, entity_id: str, relationship: EngineeringRelationship) -> tuple[str, ...]:
        return tuple(
            edge.target_id
            for edge in self._edges
            if edge.source_id == entity_id and edge.relationship is relationship
        )

    @property
    def edges(self) -> tuple[ConceptEdge, ...]:
        return tuple(self._edges)
