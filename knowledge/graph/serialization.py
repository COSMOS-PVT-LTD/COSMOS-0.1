"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.serialization

Purpose:
    Deterministic serialization helpers for graph records.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from knowledge.graph.contracts import (
    GraphNode,
    GraphNodeIdentity,
    GraphRelationship,
    ImmutableGraphRecord,
    PropertyValue,
)
from knowledge.graph.exceptions import GraphValidationError

__all__ = (
    "canonical_graph_record_digest",
    "graph_record_from_mapping",
    "graph_record_to_mapping",
)


def graph_record_to_mapping(
    record: ImmutableGraphRecord,
) -> dict[str, object]:
    """
    Serialize a graph record to a deterministic mapping.

    Nodes and relationships are ordered by identifier for reproducibility.
    """

    nodes = sorted(
        record.nodes,
        key=lambda node: (node.node_id, node.node_type),
    )
    relationships = sorted(
        record.relationships,
        key=lambda relationship: relationship.relationship_id,
    )

    return {
        "nodes": [node.to_mapping() for node in nodes],
        "relationships": [
            relationship.to_mapping()
            for relationship in relationships
        ],
    }


def _properties_from_mapping(
    raw_properties: object,
) -> dict[str, PropertyValue]:
    if raw_properties is None:
        return {}

    if not isinstance(raw_properties, Mapping):
        raise GraphValidationError("Node properties must be a mapping.")

    normalized: dict[str, PropertyValue] = {}

    for key, value in raw_properties.items():
        if not isinstance(key, str):
            raise GraphValidationError(
                "Node property keys must be strings."
            )

        if value is not None and not isinstance(
            value,
            (str, int, float, bool),
        ):
            raise GraphValidationError(
                f"Node property '{key}' has an unsupported type."
            )

        normalized[key] = value  # type: ignore[assignment]

    return normalized


def _node_from_mapping(data: Mapping[str, object]) -> GraphNode:
    node_id = data.get("node_id")
    node_type = data.get("node_type")

    if not isinstance(node_id, str) or not isinstance(node_type, str):
        raise GraphValidationError(
            "Node mapping must include string node_id and node_type."
        )

    properties = _properties_from_mapping(data.get("properties", {}))

    return GraphNode(
        identity=GraphNodeIdentity(
            node_id=node_id,
            node_type=node_type,
        ),
        properties=properties,
    )


def _relationship_from_mapping(
    data: Mapping[str, object],
) -> GraphRelationship:
    required_fields = (
        "relationship_id",
        "relationship_type",
        "source_node_id",
        "target_node_id",
    )

    values: dict[str, str] = {}

    for field_name in required_fields:
        value = data.get(field_name)

        if not isinstance(value, str):
            raise GraphValidationError(
                f"Relationship mapping must include string {field_name}."
            )

        values[field_name] = value

    properties = _properties_from_mapping(data.get("properties", {}))

    return GraphRelationship(
        relationship_id=values["relationship_id"],
        relationship_type=values["relationship_type"],
        source_node_id=values["source_node_id"],
        target_node_id=values["target_node_id"],
        properties=properties,
    )


def graph_record_from_mapping(
    data: Mapping[str, object],
) -> ImmutableGraphRecord:
    """Deserialize a graph record mapping into an immutable graph record."""

    raw_nodes = data.get("nodes")
    raw_relationships = data.get("relationships")

    if not isinstance(raw_nodes, list):
        raise GraphValidationError("Graph record mapping must include nodes.")

    if not isinstance(raw_relationships, list):
        raise GraphValidationError(
            "Graph record mapping must include relationships."
        )

    nodes = tuple(
        _node_from_mapping(node_data)
        for node_data in raw_nodes
        if isinstance(node_data, Mapping)
    )

    if len(nodes) != len(raw_nodes):
        raise GraphValidationError("Each node entry must be a mapping.")

    relationships = tuple(
        _relationship_from_mapping(relationship_data)
        for relationship_data in raw_relationships
        if isinstance(relationship_data, Mapping)
    )

    if len(relationships) != len(raw_relationships):
        raise GraphValidationError(
            "Each relationship entry must be a mapping."
        )

    return ImmutableGraphRecord(
        nodes=nodes,
        relationships=relationships,
    )


def canonical_graph_record_digest(
    record: ImmutableGraphRecord,
) -> str:
    """Return a deterministic SHA-256 digest for a graph record."""

    canonical_mapping = graph_record_to_mapping(record)
    canonical_json = json.dumps(
        canonical_mapping,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
