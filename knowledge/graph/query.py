"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.query

Purpose:
    Graph query and traversal operations over GraphStore backends.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from knowledge.graph.contracts import (
    GraphNode,
    GraphRelationship,
    ImmutableGraphRecord,
)
from knowledge.graph.exceptions import GraphQueryError, GraphValidationError
from knowledge.graph.repository import GraphStore

__all__ = (
    "GraphQueryService",
    "TraversalResult",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TraversalResult:
    """Bounded traversal result with visited nodes and relationships."""

    nodes: tuple[GraphNode, ...]
    relationships: tuple[GraphRelationship, ...]
    depth_by_node_id: dict[str, int]

    def to_record(self) -> ImmutableGraphRecord:
        """Materialize the traversal result as an immutable graph record."""

        return ImmutableGraphRecord(
            nodes=self.nodes,
            relationships=self.relationships,
        )


class GraphQueryService:
    """
    Storage-neutral graph query and traversal service.

    Operates over any GraphStore implementation without introducing a graph
    database dependency.
    """

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    def get_entity(self, node_id: str) -> GraphNode:
        """Return a graph node by identifier."""

        return self._store.get_node(node_id)

    def get_relationship(self, relationship_id: str) -> GraphRelationship:
        """Return a graph relationship by identifier."""

        return self._store.get_relationship(relationship_id)

    def neighbors(self, node_id: str) -> tuple[GraphNode, ...]:
        """Return directly connected neighbor nodes in deterministic order."""

        neighbor_ids = sorted(
            {
                relationship.target_node_id
                if relationship.source_node_id == node_id
                else relationship.source_node_id
                for relationship in self._store.list_relationships()
                if node_id
                in (
                    relationship.source_node_id,
                    relationship.target_node_id,
                )
            }
        )

        return tuple(self._store.get_node(neighbor_id) for neighbor_id in neighbor_ids)

    def traverse(self, start_node_id: str, max_depth: int) -> TraversalResult:
        """Traverse the graph to a bounded depth from a start node."""

        if not isinstance(max_depth, int) or isinstance(max_depth, bool):
            raise GraphValidationError("max_depth must be an integer.")

        if max_depth < 0:
            raise GraphValidationError("max_depth must be non-negative.")

        visited_nodes: dict[str, GraphNode] = {}
        visited_relationships: dict[str, GraphRelationship] = {}
        depth_by_node_id: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque([(start_node_id, 0)])

        while queue:
            current_id, depth = queue.popleft()

            if current_id in visited_nodes:
                continue

            visited_nodes[current_id] = self._store.get_node(current_id)
            depth_by_node_id[current_id] = depth

            if depth >= max_depth:
                continue

            for relationship in self._store.list_relationships():
                if relationship.source_node_id == current_id:
                    neighbor_id = relationship.target_node_id
                elif relationship.target_node_id == current_id:
                    neighbor_id = relationship.source_node_id
                else:
                    continue

                visited_relationships[relationship.relationship_id] = (
                    relationship
                )

                if neighbor_id not in visited_nodes:
                    queue.append((neighbor_id, depth + 1))

        return TraversalResult(
            nodes=tuple(
                visited_nodes[node_id]
                for node_id in sorted(visited_nodes)
            ),
            relationships=tuple(
                visited_relationships[relationship_id]
                for relationship_id in sorted(visited_relationships)
            ),
            depth_by_node_id=depth_by_node_id,
        )

    def subgraph(self, node_ids: set[str]) -> ImmutableGraphRecord:
        """Extract a subgraph containing only the requested node identifiers."""

        if not node_ids:
            return ImmutableGraphRecord(nodes=(), relationships=())

        nodes = tuple(
            self._store.get_node(node_id)
            for node_id in sorted(node_ids)
        )

        relationships = tuple(
            relationship
            for relationship in sorted(
                self._store.list_relationships(),
                key=lambda item: item.relationship_id,
            )
            if relationship.source_node_id in node_ids
            and relationship.target_node_id in node_ids
        )

        return ImmutableGraphRecord(nodes=nodes, relationships=relationships)

    def provenance_metadata(self, node_id: str) -> dict[str, object]:
        """Return provenance-oriented metadata stored on a graph node."""

        node = self._store.get_node(node_id)

        metadata: dict[str, object] = {
            "node_id": node.node_id,
            "node_type": node.node_type,
        }

        for key in (
            "document_id",
            "lifecycle_state",
            "confidence_score",
            "confidence_band",
            "conflict_visibility",
        ):
            if key in node.properties:
                metadata[key] = node.properties[key]

        if len(metadata) == 2:
            raise GraphQueryError(
                "Node does not contain provenance metadata."
            )

        return metadata
