"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.repository

Purpose:
    Storage-neutral graph store interface for Knowledge Graph persistence.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from knowledge.graph.contracts import (
    GraphNode,
    GraphRelationship,
    ImmutableGraphRecord,
)

__all__ = (
    "GraphStore",
)


@runtime_checkable
class GraphStore(Protocol):
    """
    Storage-neutral interface between graph contracts and future backends.

    Implementations must not mutate supplied contract objects.
  """

    def add_node(self, node: GraphNode) -> None:
        """Store a graph node."""

    def get_node(self, node_id: str) -> GraphNode:
        """Return a graph node by identifier."""

    def remove_node(self, node_id: str) -> None:
        """Remove a graph node by identifier."""

    def list_nodes(self) -> Sequence[GraphNode]:
        """Return all stored graph nodes in deterministic order."""

    def add_relationship(self, relationship: GraphRelationship) -> None:
        """Store a graph relationship."""

    def get_relationship(self, relationship_id: str) -> GraphRelationship:
        """Return a graph relationship by identifier."""

    def remove_relationship(self, relationship_id: str) -> None:
        """Remove a graph relationship by identifier."""

    def list_relationships(self) -> Sequence[GraphRelationship]:
        """Return all stored relationships in deterministic order."""

    def snapshot(self) -> ImmutableGraphRecord:
        """Return an immutable snapshot of the current graph state."""

    def restore(self, record: ImmutableGraphRecord) -> None:
        """Replace the current graph state with a validated record."""
