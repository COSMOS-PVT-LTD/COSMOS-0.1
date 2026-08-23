"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.relationship

Purpose:
    Graph relationship integration contracts with provenance anchors.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.contracts import (
    GraphRelationship,
    ProvenanceReference,
)
from knowledge.graph.exceptions import GraphContractError, GraphValidationError
from knowledge.graph.provenance import SourceProvenanceRecord

__all__ = (
    "GraphEntityRelationshipRecord",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphEntityRelationshipRecord:
    """
    Graph relationship adapter with optional provenance metadata.

    Endpoint identifiers must match the wrapped ``GraphRelationship`` values.
    """

    relationship: GraphRelationship
    provenance: ProvenanceReference | SourceProvenanceRecord | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.relationship, GraphRelationship):
            raise GraphValidationError(
                "relationship must be a GraphRelationship instance."
            )

        if self.provenance is not None and not isinstance(
            self.provenance,
            (ProvenanceReference, SourceProvenanceRecord),
        ):
            raise GraphValidationError(
                "provenance must be a ProvenanceReference or "
                "SourceProvenanceRecord instance."
            )

    def validate_entity_endpoints(
        self,
        source_entity_id: str,
        target_entity_id: str,
    ) -> None:
        """
        Verify adapter endpoint identifiers against entity identifiers.

        Raises
        ------
        GraphContractError
            If either endpoint does not match the relationship record.
        """

        if self.relationship.source_node_id != source_entity_id:
            raise GraphContractError(
                "Relationship source_node_id does not match source entity."
            )

        if self.relationship.target_node_id != target_entity_id:
            raise GraphContractError(
                "Relationship target_node_id does not match target entity."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "relationship": self.relationship.to_mapping(),
        }

        if isinstance(self.provenance, ProvenanceReference):
            payload["provenance"] = self.provenance.to_mapping()
        elif isinstance(self.provenance, SourceProvenanceRecord):
            payload["provenance"] = self.provenance.to_mapping()

        return payload
