"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.memory_store

Purpose:
    Reference in-memory implementation of the GraphStore protocol.
"""

from __future__ import annotations

from knowledge.graph.contracts import (
    GraphNode,
    GraphRelationship,
    ImmutableGraphRecord,
)
from knowledge.graph.exceptions import GraphStorageError

__all__ = (
    "InMemoryGraphStore",
)


class InMemoryGraphStore:
    """
    In-memory GraphStore implementation for local/offline graph operations.

    This is a reference backend, not a graph database integration.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._relationships: dict[str, GraphRelationship] = {}

    def add_node(self, node: GraphNode) -> None:
        if node.node_id in self._nodes:
            raise GraphStorageError(
                f"Node '{node.node_id}' already exists."
            )

        self._nodes[node.node_id] = node

    def get_node(self, node_id: str) -> GraphNode:
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise GraphStorageError(
                f"Node '{node_id}' was not found."
            ) from exc

    def remove_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise GraphStorageError(f"Node '{node_id}' was not found.")

        del self._nodes[node_id]

    def list_nodes(self) -> tuple[GraphNode, ...]:
        return tuple(
            self._nodes[node_id] for node_id in sorted(self._nodes)
        )

    def add_relationship(self, relationship: GraphRelationship) -> None:
        if relationship.relationship_id in self._relationships:
            raise GraphStorageError(
                "Relationship "
                f"'{relationship.relationship_id}' already exists."
            )

        if relationship.source_node_id not in self._nodes:
            raise GraphStorageError(
                "Relationship source node must exist before insertion."
            )

        if relationship.target_node_id not in self._nodes:
            raise GraphStorageError(
                "Relationship target node must exist before insertion."
            )

        self._relationships[relationship.relationship_id] = relationship

    def get_relationship(self, relationship_id: str) -> GraphRelationship:
        try:
            return self._relationships[relationship_id]
        except KeyError as exc:
            raise GraphStorageError(
                f"Relationship '{relationship_id}' was not found."
            ) from exc

    def remove_relationship(self, relationship_id: str) -> None:
        if relationship_id not in self._relationships:
            raise GraphStorageError(
                f"Relationship '{relationship_id}' was not found."
            )

        del self._relationships[relationship_id]

    def list_relationships(self) -> tuple[GraphRelationship, ...]:
        return tuple(
            self._relationships[relationship_id]
            for relationship_id in sorted(self._relationships)
        )

    def snapshot(self) -> ImmutableGraphRecord:
        return ImmutableGraphRecord(
            nodes=self.list_nodes(),
            relationships=self.list_relationships(),
        )

    def restore(self, record: ImmutableGraphRecord) -> None:
        self._nodes = {node.node_id: node for node in record.nodes}
        self._relationships = {
            relationship.relationship_id: relationship
            for relationship in record.relationships
        }
