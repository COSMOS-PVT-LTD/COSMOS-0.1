"""Graph index for KG-035 (W7)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, TypedDict

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexNotFoundError, IndexStaleError, IndexValidationError
from knowledge.indexing.models import IndexLifecycleState, IndexMetadata, IndexStatistics

__all__ = (
    "GraphIndexAdjacency",
    "GraphIndex",
    "InMemoryGraphIndex",
    "build_graph_index_from_store",
    "require_fresh_graph_index",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphIndexAdjacency:
    """Deterministic adjacency record for a graph node."""

    node_id: str
    node_type: str
    neighbor_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    document_id: str | None = None
    lifecycle_state: str | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise IndexValidationError("node_id must not be blank.")

        if not self.node_type.strip():
            raise IndexValidationError("node_type must not be blank.")


class GraphIndex(Protocol):
    """Backend-neutral graph adjacency index contract."""

    def metadata(self) -> IndexMetadata:
        """Return index metadata."""

    def statistics(self) -> IndexStatistics:
        """Return aggregate index statistics."""

    def adjacency(self) -> tuple[GraphIndexAdjacency, ...]:
        """Return adjacency records in deterministic order."""

    def neighbors(self, node_id: str) -> tuple[str, ...]:
        """Return sorted neighbor node IDs for a node."""

    def is_stale(self, source_digest: str) -> bool:
        """Return True when the index is stale relative to source knowledge."""


class InMemoryGraphIndex:
    """Reference in-memory graph adjacency index."""

    def __init__(
        self,
        *,
        index_id: str,
        source_digest: str,
        adjacency_records: Sequence[GraphIndexAdjacency],
    ) -> None:
        self._index_id = index_id.strip()
        self._source_digest = source_digest.strip()
        sorted_records = tuple(
            sorted(adjacency_records, key=lambda item: item.node_id),
        )
        seen_node_ids: set[str] = set()

        for record in sorted_records:
            if record.node_id in seen_node_ids:
                raise IndexValidationError(
                    f"Duplicate graph index node_id '{record.node_id}'.",
                )

            seen_node_ids.add(record.node_id)

        self._records = sorted_records
        self._adjacency_by_node = {
            record.node_id: record for record in self._records
        }

    def metadata(self) -> IndexMetadata:
        return IndexMetadata(
            index_id=self._index_id,
            source_digest=self._source_digest,
            entry_count=len(self._records),
            lifecycle_state=IndexLifecycleState.VALID,
        )

    def statistics(self) -> IndexStatistics:
        relationship_count = sum(
            len(record.relationship_ids) for record in self._records
        )

        return IndexStatistics(
            entry_count=len(self._records),
            unique_term_count=relationship_count,
            target_count=len(self._records),
        )

    def adjacency(self) -> tuple[GraphIndexAdjacency, ...]:
        return self._records

    def neighbors(self, node_id: str) -> tuple[str, ...]:
        record = self._adjacency_by_node.get(node_id)

        if record is None:
            raise IndexNotFoundError(
                f"Graph index node '{node_id}' was not found.",
            )

        return record.neighbor_ids

    def is_stale(self, source_digest: str) -> bool:
        return self._source_digest != source_digest.strip()


class _AdjacencyBuilderEntry(TypedDict):
    node_type: str
    neighbor_ids: set[str]
    relationship_ids: set[str]
    document_id: str | None
    lifecycle_state: str | None


def build_graph_index_from_store(
    store: GraphStore,
    *,
    index_id: str = "graph-default",
) -> InMemoryGraphIndex:
    """Build a graph adjacency index from authoritative graph knowledge."""

    record = store.snapshot()
    source_digest = canonical_graph_record_digest(record)
    node_ids = {node.node_id for node in record.nodes}
    adjacency_by_node: dict[str, _AdjacencyBuilderEntry] = {}

    for node in sorted(record.nodes, key=lambda item: item.node_id):
        lifecycle_value = node.properties.get("lifecycle_state")
        document_id = node.properties.get("document_id")

        adjacency_by_node[node.node_id] = {
            "node_type": node.node_type,
            "neighbor_ids": set(),
            "relationship_ids": set(),
            "document_id": str(document_id)
            if isinstance(document_id, str)
            else None,
            "lifecycle_state": str(lifecycle_value)
            if lifecycle_value is not None
            else None,
        }

    for relationship in sorted(
        record.relationships,
        key=lambda item: item.relationship_id,
    ):
        source_id = relationship.source_node_id
        target_id = relationship.target_node_id

        if source_id not in node_ids or target_id not in node_ids:
            raise IndexValidationError(
                "Graph index build encountered dangling relationship endpoint.",
            )

        for node_id, neighbor_id in (
            (source_id, target_id),
            (target_id, source_id),
        ):
            node_entry = adjacency_by_node[node_id]
            node_entry["neighbor_ids"].add(neighbor_id)
            node_entry["relationship_ids"].add(relationship.relationship_id)

    records = tuple(
        GraphIndexAdjacency(
            node_id=node_id,
            node_type=entry["node_type"],
            neighbor_ids=tuple(sorted(entry["neighbor_ids"])),
            relationship_ids=tuple(sorted(entry["relationship_ids"])),
            document_id=entry["document_id"],
            lifecycle_state=entry["lifecycle_state"],
        )
        for node_id, entry in sorted(adjacency_by_node.items())
    )

    return InMemoryGraphIndex(
        index_id=index_id,
        source_digest=source_digest,
        adjacency_records=records,
    )


def require_fresh_graph_index(
    index: GraphIndex,
    source_digest: str,
) -> None:
    """Raise when the graph index is stale."""

    if index.is_stale(source_digest):
        raise IndexStaleError(
            "Graph index is stale relative to authoritative knowledge.",
        )
