"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.contracts

Purpose:
    Storage-neutral graph contracts for the COSMOS Knowledge Graph.

Description:
    Defines deterministic identity, node and relationship records, provenance
    references, and graph containers. These contracts use opaque identifiers
    and do not embed canonical domain model instances from knowledge.models.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from knowledge.graph.exceptions import GraphValidationError

__all__ = (
    "GraphNode",
    "GraphNodeIdentity",
    "GraphRecord",
    "GraphRelationship",
    "ProvenanceReference",
    "PropertyValue",
    "is_property_value",
    "normalize_properties",
)

PropertyValue = str | int | float | bool | None

_ALLOWED_PROPERTY_TYPES = (str, int, float, bool, type(None))


def is_property_value(value: object) -> bool:
    """Return True if value is an allowed graph property value."""

    return isinstance(value, _ALLOWED_PROPERTY_TYPES)


def normalize_properties(
    properties: Mapping[str, object] | None,
) -> Mapping[str, PropertyValue]:
    """
    Normalize and validate a property mapping for graph contracts.

    Raises
    ------
    GraphValidationError
        If a key is blank or a value has an unsupported type.
    """

    if properties is None:
        return MappingProxyType({})

    normalized: dict[str, PropertyValue] = {}

    for key, value in properties.items():
        if not isinstance(key, str) or not key.strip():
            raise GraphValidationError(
                "Graph property keys must be non-blank strings."
            )

        if not is_property_value(value):
            raise GraphValidationError(
                f"Graph property '{key}' has unsupported type "
                f"{type(value).__name__}."
            )

        normalized[key] = value  # type: ignore[assignment]

    return MappingProxyType(normalized)


def _validate_non_empty_string(
    field_name: str,
    value: str,
) -> str:
    if not isinstance(value, str):
        raise GraphValidationError(
            f"{field_name} must be a string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise GraphValidationError(
            f"{field_name} must not be blank."
        )

    return cleaned


def _validate_optional_positive_int(
    field_name: str,
    value: int | None,
) -> int | None:
    if value is None:
        return None

    if not isinstance(value, int) or isinstance(value, bool):
        raise GraphValidationError(
            f"{field_name} must be an integer."
        )

    if value <= 0:
        raise GraphValidationError(
            f"{field_name} must be a positive integer."
        )

    return value


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)


@dataclass(frozen=True, slots=True)
class GraphNodeIdentity:
    """
    Deterministic identity for a graph node.

    Identity depends only on explicit node_id and node_type values, not on
    process-local object identity or random identifiers.
    """

    node_id: str
    node_type: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "node_id",
            _validate_non_empty_string("node_id", self.node_id),
        )
        object.__setattr__(
            self,
            "node_type",
            _validate_non_empty_string("node_type", self.node_type),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphNode:
    """
    Minimal graph node record.

    The contract stores opaque identity and optional scalar properties only.
    It does not embed canonical domain model instances.

    Equality and hashing are structural value semantics: two ``GraphNode``
    instances compare equal when both ``identity`` and ``properties`` match.
    Scalar properties therefore participate in equality; nodes that share the
    same ``GraphNodeIdentity`` but differ in ``properties`` are not equal.
    """

    identity: GraphNodeIdentity
    properties: Mapping[str, PropertyValue] = field(
        default_factory=lambda: MappingProxyType({}),
    )

    def __post_init__(self) -> None:
        if not isinstance(self.identity, GraphNodeIdentity):
            raise GraphValidationError(
                "identity must be a GraphNodeIdentity instance."
            )

        normalized = normalize_properties(self.properties)

        if normalized is not self.properties:
            object.__setattr__(self, "properties", normalized)

    @property
    def node_id(self) -> str:
        """Return the node identifier."""

        return self.identity.node_id

    @property
    def node_type(self) -> str:
        """Return the node type."""

        return self.identity.node_type

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "properties": dict(self.properties),
        }

    def __hash__(self) -> int:
        return hash(
            (
                self.identity,
                tuple(sorted(self.properties.items())),
            )
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphRelationship:
    """
    Directed graph relationship between two node identifiers.
    """

    relationship_id: str
    relationship_type: str
    source_node_id: str
    target_node_id: str
    properties: Mapping[str, PropertyValue] = field(
        default_factory=lambda: MappingProxyType({}),
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relationship_id",
            _validate_non_empty_string(
                "relationship_id",
                self.relationship_id,
            ),
        )
        object.__setattr__(
            self,
            "relationship_type",
            _validate_non_empty_string(
                "relationship_type",
                self.relationship_type,
            ),
        )
        object.__setattr__(
            self,
            "source_node_id",
            _validate_non_empty_string(
                "source_node_id",
                self.source_node_id,
            ),
        )
        object.__setattr__(
            self,
            "target_node_id",
            _validate_non_empty_string(
                "target_node_id",
                self.target_node_id,
            ),
        )

        normalized = normalize_properties(self.properties)

        if normalized is not self.properties:
            object.__setattr__(self, "properties", normalized)

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "relationship_id": self.relationship_id,
            "relationship_type": self.relationship_type,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "properties": dict(self.properties),
        }

    def __hash__(self) -> int:
        return hash(
            (
                self.relationship_id,
                self.relationship_type,
                self.source_node_id,
                self.target_node_id,
                tuple(sorted(self.properties.items())),
            )
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProvenanceReference:
    """
    Lightweight provenance anchor without embedded source text.

    At least one anchor field must be populated.
    """

    source_id: str | None = None
    document_id: str | None = None
    page: int | None = None
    section: str | None = None
    paragraph: str | None = None
    figure: str | None = None
    table: str | None = None
    equation: str | None = None
    location_anchor: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _validate_optional_non_empty_string(
                "source_id",
                self.source_id,
            ),
        )
        object.__setattr__(
            self,
            "document_id",
            _validate_optional_non_empty_string(
                "document_id",
                self.document_id,
            ),
        )
        object.__setattr__(
            self,
            "page",
            _validate_optional_positive_int("page", self.page),
        )
        object.__setattr__(
            self,
            "section",
            _validate_optional_non_empty_string(
                "section",
                self.section,
            ),
        )
        object.__setattr__(
            self,
            "paragraph",
            _validate_optional_non_empty_string(
                "paragraph",
                self.paragraph,
            ),
        )
        object.__setattr__(
            self,
            "figure",
            _validate_optional_non_empty_string("figure", self.figure),
        )
        object.__setattr__(
            self,
            "table",
            _validate_optional_non_empty_string("table", self.table),
        )
        object.__setattr__(
            self,
            "equation",
            _validate_optional_non_empty_string(
                "equation",
                self.equation,
            ),
        )
        object.__setattr__(
            self,
            "location_anchor",
            _validate_optional_non_empty_string(
                "location_anchor",
                self.location_anchor,
            ),
        )

        if not any(
            getattr(self, provenance_field.name) is not None
            for provenance_field in fields(self)
        ):
            raise GraphValidationError(
                "ProvenanceReference requires at least one anchor field."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            field_def.name: getattr(self, field_def.name)
            for field_def in fields(self)
            if getattr(self, field_def.name) is not None
        }


@runtime_checkable
class GraphRecord(Protocol):
    """
    Storage-neutral container for graph nodes and relationships.
    """

    @property
    def nodes(self) -> Sequence[GraphNode]:
        """Return graph nodes."""

    @property
    def relationships(self) -> Sequence[GraphRelationship]:
        """Return graph relationships."""


@dataclass(frozen=True, slots=True)
class ImmutableGraphRecord:
    """
    Immutable in-memory graph record implementing GraphRecord.

    Endpoint referential integrity (relationship ``source_node_id`` and
    ``target_node_id`` must reference existing node identifiers) applies to
    validated graph records and snapshots. It is not intended to prescribe
    incremental graph-construction semantics; builders in later KG batches may
    assemble partial graphs before validation.
    """

    nodes: tuple[GraphNode, ...]
    relationships: tuple[GraphRelationship, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, tuple):
            raise GraphValidationError("nodes must be a tuple.")

        if not isinstance(self.relationships, tuple):
            raise GraphValidationError(
                "relationships must be a tuple."
            )

        for index, node in enumerate(self.nodes):
            if not isinstance(node, GraphNode):
                raise GraphValidationError(
                    f"nodes[{index}] must be a GraphNode."
                )

        for index, relationship in enumerate(self.relationships):
            if not isinstance(relationship, GraphRelationship):
                raise GraphValidationError(
                    f"relationships[{index}] must be a "
                    "GraphRelationship."
                )

        node_ids = {node.node_id for node in self.nodes}

        if len(node_ids) != len(self.nodes):
            raise GraphValidationError(
                "Graph node identifiers must be unique."
            )

        for relationship in self.relationships:
            if relationship.source_node_id not in node_ids:
                raise GraphValidationError(
                    "Relationship source_node_id must reference "
                    "an existing node."
                )

            if relationship.target_node_id not in node_ids:
                raise GraphValidationError(
                    "Relationship target_node_id must reference "
                    "an existing node."
                )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "nodes": [node.to_mapping() for node in self.nodes],
            "relationships": [
                relationship.to_mapping()
                for relationship in self.relationships
            ],
        }
