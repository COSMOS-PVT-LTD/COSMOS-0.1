"""Typed engineering-graph views over the concept graph."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.concept_graph import ConceptEdge, ConceptGraph
from knowledge.graph.integrity import GraphIntegrityReport, validate_concept_graph
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship

__all__ = ("EngineeringGraphBundle", "GraphQuery", "build_engineering_graph_bundle")


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphQuery:
    entity_id: str
    relationship: EngineeringRelationship


@dataclass(frozen=True, slots=True, kw_only=True)
class EngineeringGraphBundle:
    concept: ConceptGraph
    integrity: GraphIntegrityReport

    def related(self, entity_id: str, relationship: EngineeringRelationship) -> tuple[str, ...]:
        return self.concept.related(entity_id, relationship)

    def uses(self, entity_id: str) -> tuple[str, ...]:
        return self.concept.related(entity_id, EngineeringRelationship.USES)

    def validated_by(self, entity_id: str) -> tuple[str, ...]:
        return self.concept.related(entity_id, EngineeringRelationship.VALIDATED_BY)

    def valid_for(self, entity_id: str) -> tuple[str, ...]:
        return self.concept.related(entity_id, EngineeringRelationship.VALID_FOR)

    def requires(self, entity_id: str) -> tuple[str, ...]:
        return self.concept.related(entity_id, EngineeringRelationship.REQUIRES)


def build_engineering_graph_bundle(
    edges: tuple[ConceptEdge, ...],
    known_ids: frozenset[str],
) -> EngineeringGraphBundle:
    graph = ConceptGraph()
    for edge in edges:
        graph.add(edge)
    return EngineeringGraphBundle(
        concept=graph,
        integrity=validate_concept_graph(graph, known_ids),
    )
