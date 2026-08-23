"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-004).

Frozen Part-3 graph manager surface delegating to GraphConstructor and GraphQueryService.
"""

from __future__ import annotations

from knowledge.graph.construction import (
    GraphConstructionBatch,
    GraphConstructionResult,
    GraphConstructor,
)
from knowledge.graph.exceptions import GraphQueryError
from knowledge.graph.query import GraphQueryService, TraversalResult
from knowledge.graph.repository import GraphStore
from knowledge.ontology.registry import OntologyRegistry

__all__ = ("GraphManager",)


class GraphManager:
    """Unified graph manager facade over canonical construction and query services."""

    def __init__(self, ontology_registry: OntologyRegistry | None = None) -> None:
        self._ontology_registry = ontology_registry or OntologyRegistry()
        self._constructor = GraphConstructor(self._ontology_registry)
        self._store: GraphStore | None = None
        self._query: GraphQueryService | None = None

    def construct(
        self,
        batch: GraphConstructionBatch,
        *,
        snapshot_sequence: int = 1,
    ) -> GraphConstructionResult:
        result = self._constructor.construct(
            batch,
            snapshot_sequence=snapshot_sequence,
        )
        self._store = result.store
        self._query = GraphQueryService(result.store)
        return result

    def query_service(self) -> GraphQueryService:
        if self._query is None:
            raise GraphQueryError(
                "GraphManager has no constructed graph. Call construct() first.",
            )
        return self._query

    def traverse(
        self,
        start_node_id: str,
        *,
        max_depth: int = 2,
    ) -> TraversalResult:
        return self.query_service().traverse(
            start_node_id,
            max_depth=max_depth,
        )

    @property
    def store(self) -> GraphStore:
        if self._store is None:
            raise GraphQueryError(
                "GraphManager has no constructed graph. Call construct() first.",
            )
        return self._store

    @property
    def ontology_registry(self) -> OntologyRegistry:
        return self._ontology_registry
