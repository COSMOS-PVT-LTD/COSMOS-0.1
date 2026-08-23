"""
COSMOS Knowledge Foundation — Knowledge Graph contracts.

This package provides storage-neutral graph contracts used by downstream
Knowledge Graph batches. It does not implement ingestion, storage engines,
vector search, or reasoning.
"""

from __future__ import annotations

from knowledge.graph.contracts import (
    GraphNode,
    GraphNodeIdentity,
    GraphRecord,
    GraphRelationship,
    ImmutableGraphRecord,
    ProvenanceReference,
    PropertyValue,
    is_property_value,
    normalize_properties,
)
from knowledge.graph.entity import (
    CANONICAL_MODEL_NAMES,
    CanonicalEntityReference,
    CanonicalEntityType,
    GraphEntityRecord,
)
from knowledge.graph.exceptions import (
    GraphContractError,
    GraphConstructionError,
    GraphError,
    GraphQueryError,
    GraphStorageError,
    GraphValidationError,
)
from knowledge.graph.lifecycle import (
    GraphLifecycleMetadata,
    GraphLifecycleState,
    GraphLifecycleTransitionError,
    allowed_lifecycle_targets,
    is_terminal_lifecycle_state,
    transition_lifecycle_state,
)
from knowledge.graph.provenance import (
    ExtractionProvenance,
    ReviewStatus,
    SourceLineage,
    SourceProvenanceRecord,
)
from knowledge.graph.relationship import GraphEntityRelationshipRecord
from knowledge.graph.memory_store import InMemoryGraphStore
from knowledge.graph.query import GraphQueryService, TraversalResult
from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import (
    canonical_graph_record_digest,
    graph_record_from_mapping,
    graph_record_to_mapping,
)
from knowledge.graph.snapshot import (
    GraphSnapshot,
    GraphSnapshotIdentity,
    GraphSnapshotMetadata,
    build_snapshot_id,
    create_graph_snapshot,
    snapshots_are_equivalent,
)
from knowledge.graph.validation import (
    GraphRecordValidationIssue,
    GraphRecordValidationReport,
    GraphRecordValidator,
)
from knowledge.graph.source_identity import (
    ArtifactIdentity,
    SourceIdentity,
    SourceStatus,
    SourceType,
    is_valid_sha256_hex,
)

__all__ = (
    "ArtifactIdentity",
    "CANONICAL_MODEL_NAMES",
    "CanonicalEntityReference",
    "CanonicalEntityType",
    "ExtractionProvenance",
    "GraphConstructionBatch",
    "GraphConstructionError",
    "GraphConstructionResult",
    "GraphConstructor",
    "GraphContractError",
    "GraphEntityRecord",
    "GraphEntityRelationshipRecord",
    "GraphError",
    "GraphLifecycleMetadata",
    "GraphLifecycleState",
    "GraphLifecycleTransitionError",
    "GraphNode",
    "GraphNodeIdentity",
    "GraphQueryError",
    "GraphQueryService",
    "GraphRecord",
    "GraphRecordValidationIssue",
    "GraphRecordValidationReport",
    "GraphRecordValidator",
    "GraphRelationship",
    "GraphSnapshot",
    "GraphSnapshotIdentity",
    "GraphSnapshotMetadata",
    "GraphStorageError",
    "GraphStore",
    "GraphValidationError",
    "ImmutableGraphRecord",
    "InMemoryGraphStore",
    "ProvenanceReference",
    "PropertyValue",
    "ReviewStatus",
    "SourceIdentity",
    "SourceLineage",
    "SourceProvenanceRecord",
    "SourceStatus",
    "SourceType",
    "TraversalResult",
    "allowed_lifecycle_targets",
    "build_snapshot_id",
    "canonical_graph_record_digest",
    "create_graph_snapshot",
    "graph_node_id_for_extraction",
    "graph_record_from_mapping",
    "graph_record_to_mapping",
    "is_property_value",
    "is_terminal_lifecycle_state",
    "is_valid_sha256_hex",
    "normalize_properties",
    "snapshots_are_equivalent",
    "transition_lifecycle_state",
)

_LAZY_ATTRS: dict[str, tuple[str, str]] = {
    "GraphConstructionBatch": (
        "knowledge.graph.construction",
        "GraphConstructionBatch",
    ),
    "GraphConstructionResult": (
        "knowledge.graph.construction",
        "GraphConstructionResult",
    ),
    "GraphConstructor": (
        "knowledge.graph.construction",
        "GraphConstructor",
    ),
    "graph_node_id_for_extraction": (
        "knowledge.graph.construction",
        "graph_node_id_for_extraction",
    ),
}


def __getattr__(name: str) -> object:
    """Lazily import construction symbols to avoid extraction import cycles."""

    if name in _LAZY_ATTRS:
        import importlib

        module_name, attr_name = _LAZY_ATTRS[name]
        module = importlib.import_module(module_name)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
