"""Graph integrity checks for engineering concept graphs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from knowledge.graph.concept_graph import ConceptGraph
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship

__all__ = ("GraphIntegrityReport", "validate_concept_graph")

_ACYCLIC = frozenset(
    {
        EngineeringRelationship.IS_A,
        EngineeringRelationship.PART_OF,
        EngineeringRelationship.DEPENDS_ON,
        EngineeringRelationship.SUPERSEDES,
        EngineeringRelationship.DERIVED_FROM,
    },
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphIntegrityReport:
    passed: bool
    orphan_targets: tuple[str, ...]
    invalid_relationships: tuple[str, ...]
    duplicate_edges: int
    missing_source_nodes: tuple[str, ...] = ()
    illegal_cycles: tuple[str, ...] = ()
    contradictory_pairs: tuple[str, ...] = ()


def validate_concept_graph(graph: ConceptGraph, known_ids: frozenset[str]) -> GraphIntegrityReport:
    seen: set[tuple[str, str, str]] = set()
    duplicates = 0
    orphans: list[str] = []
    missing_sources: list[str] = []
    invalid: list[str] = []
    adjacency: dict[str, list[str]] = defaultdict(list)
    contradicts: list[str] = []

    for edge in graph._edges:
        key = (edge.source_id, edge.target_id, edge.relationship.value)
        if key in seen:
            duplicates += 1
        seen.add(key)
        if edge.source_id not in known_ids:
            missing_sources.append(edge.source_id)
        if edge.target_id not in known_ids:
            orphans.append(edge.target_id)
        if not isinstance(edge.relationship, EngineeringRelationship):
            invalid.append(edge.source_id)
        if edge.relationship in _ACYCLIC:
            adjacency[edge.source_id].append(edge.target_id)
        if edge.relationship is EngineeringRelationship.CONTRADICTS:
            contradicts.append(f"{edge.source_id}->{edge.target_id}")

    cycles = _detect_cycles(adjacency)
    passed = not orphans and not invalid and not missing_sources and not cycles and duplicates == 0
    return GraphIntegrityReport(
        passed=passed,
        orphan_targets=tuple(sorted(set(orphans))),
        invalid_relationships=tuple(sorted(set(invalid))),
        duplicate_edges=duplicates,
        missing_source_nodes=tuple(sorted(set(missing_sources))),
        illegal_cycles=tuple(sorted(cycles)),
        contradictory_pairs=tuple(sorted(set(contradicts))),
    )


def _detect_cycles(adjacency: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[str] = []

    def walk(node: str, path: list[str]) -> None:
        if node in visiting:
            start = path.index(node) if node in path else 0
            cycles.append(" > ".join([*path[start:], node]))
            return
        if node in visited:
            return
        visiting.add(node)
        for child in adjacency.get(node, ()):
            walk(child, [*path, node])
        visiting.remove(node)
        visited.add(node)

    for root in sorted(adjacency):
        walk(root, [])
    return cycles
