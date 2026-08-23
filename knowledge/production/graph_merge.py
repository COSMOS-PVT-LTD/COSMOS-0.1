"""Document-scoped graph merge for multi-document production ingestion (Step 7)."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.contracts import GraphNode, GraphRelationship, ImmutableGraphRecord
from knowledge.graph.exceptions import GraphStorageError
from knowledge.graph.memory_store import InMemoryGraphStore

__all__ = (
    "DocumentGraphMerger",
    "GraphMergeResult",
)


def _node_document_id(node: GraphNode) -> str | None:
    document_id = node.properties.get("document_id")

    if isinstance(document_id, str) and document_id.strip():
        return document_id

    return None


def _relationship_document_id(relationship: GraphRelationship) -> str | None:
    document_id = relationship.properties.get("document_id")

    if isinstance(document_id, str) and document_id.strip():
        return document_id

    return None


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphMergeResult:
    """Outcome of merging a document subgraph into a multi-document store."""

    document_id: str
    removed_nodes: int
    removed_relationships: int
    added_nodes: int
    added_relationships: int
    cross_document_conflicts: tuple[str, ...] = ()

    @property
    def success(self) -> bool:
        return not self.cross_document_conflicts


class DocumentGraphMerger:
    """Merge document-scoped graph snapshots without cross-document corruption."""

    def merge_document(
        self,
        target: InMemoryGraphStore,
        incoming: ImmutableGraphRecord,
        *,
        document_id: str,
    ) -> GraphMergeResult:
        """Replace document-scoped nodes/relationships and merge the incoming snapshot."""

        removed_nodes = 0
        removed_relationships = 0
        added_nodes = 0
        added_relationships = 0
        conflicts: list[str] = []

        existing_node_ids = [
            node.node_id
            for node in target.list_nodes()
            if _node_document_id(node) == document_id
        ]
        existing_node_id_set = set(existing_node_ids)

        relationship_ids_to_remove: list[str] = []
        for relationship in target.list_relationships():
            if (
                relationship.source_node_id in existing_node_id_set
                or relationship.target_node_id in existing_node_id_set
            ):
                relationship_ids_to_remove.append(relationship.relationship_id)
                continue

            if _relationship_document_id(relationship) == document_id:
                relationship_ids_to_remove.append(relationship.relationship_id)

        for relationship_id in sorted(set(relationship_ids_to_remove)):
            target.remove_relationship(relationship_id)
            removed_relationships += 1

        for node_id in sorted(existing_node_ids):
            target.remove_node(node_id)
            removed_nodes += 1

        for node in incoming.nodes:
            node_doc = _node_document_id(node)

            if node_doc != document_id:
                conflicts.append(
                    f"Incoming node '{node.node_id}' has document_id "
                    f"'{node_doc}', expected '{document_id}'.",
                )
                continue

            try:
                existing = target.get_node(node.node_id)
            except GraphStorageError:
                target.add_node(node)
                added_nodes += 1
                continue

            existing_doc = _node_document_id(existing)

            if existing_doc != document_id:
                conflicts.append(
                    f"Node '{node.node_id}' already exists for document "
                    f"'{existing_doc}'.",
                )
                continue

            target.remove_node(node.node_id)
            target.add_node(node)
            added_nodes += 1

        for relationship in incoming.relationships:
            try:
                target.add_relationship(relationship)
                added_relationships += 1
            except GraphStorageError as exc:
                conflicts.append(str(exc))

        return GraphMergeResult(
            document_id=document_id,
            removed_nodes=removed_nodes,
            removed_relationships=removed_relationships,
            added_nodes=added_nodes,
            added_relationships=added_relationships,
            cross_document_conflicts=tuple(conflicts),
        )

    def remove_document(
        self,
        target: InMemoryGraphStore,
        *,
        document_id: str,
    ) -> GraphMergeResult:
        """Remove all graph content scoped to a document."""

        return self.merge_document(
            target,
            ImmutableGraphRecord(nodes=(), relationships=()),
            document_id=document_id,
        )
