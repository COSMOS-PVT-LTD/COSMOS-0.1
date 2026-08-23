"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.entity

Purpose:
    Graph entity integration contracts referencing canonical COSMOS models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.contracts import GraphNode
from knowledge.graph.exceptions import GraphContractError, GraphValidationError

__all__ = (
    "CanonicalEntityReference",
    "CanonicalEntityType",
    "GraphEntityRecord",
    "CANONICAL_MODEL_NAMES",
)

CANONICAL_MODEL_NAMES: frozenset[str] = frozenset(
    {
        "constant",
        "dimension",
        "document",
        "engineering_domain",
        "equation",
        "material",
        "quantity",
        "reference",
        "subsystem",
        "unit",
        "variable",
    }
)


class CanonicalEntityType(Enum):
    """Canonical COSMOS knowledge-model entity classifications."""

    REFERENCE = "Reference"
    DOCUMENT = "Document"
    EQUATION = "Equation"
    VARIABLE = "Variable"
    QUANTITY = "Quantity"
    UNIT = "Unit"
    DIMENSION = "Dimension"
    CONSTANT = "Constant"
    MATERIAL = "Material"
    SUBSYSTEM = "Subsystem"
    ENGINEERING_DOMAIN = "EngineeringDomain"
    CLAIM = "Claim"
    OTHER = "Other"


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise GraphValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise GraphValidationError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalEntityReference:
    """
    Opaque reference to a canonical COSMOS knowledge-model entity.

    This contract does not import or embed domain model instances.
    """

    entity_id: str
    entity_type: CanonicalEntityType
    model_name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "entity_id",
            _validate_non_empty_string("entity_id", self.entity_id),
        )

        if not isinstance(self.entity_type, CanonicalEntityType):
            raise GraphValidationError(
                "entity_type must be a CanonicalEntityType value."
            )

        cleaned_model_name = _validate_non_empty_string(
            "model_name",
            self.model_name,
        )

        if cleaned_model_name not in CANONICAL_MODEL_NAMES:
            raise GraphValidationError(
                f"model_name '{cleaned_model_name}' is not a recognized "
                "canonical knowledge model."
            )

        object.__setattr__(self, "model_name", cleaned_model_name)

    def identity_key(self) -> tuple[str, str, str]:
        """Return the deterministic identity key for this reference."""

        return (
            self.entity_id,
            self.entity_type.value,
            self.model_name,
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "model_name": self.model_name,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphEntityRecord:
    """
    Graph entity adapter binding a graph node to an optional canonical reference.

    When a canonical reference is present, ``node.node_type`` must match
    ``canonical_reference.entity_type.value``.
    """

    node: GraphNode
    canonical_reference: CanonicalEntityReference | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.node, GraphNode):
            raise GraphValidationError("node must be a GraphNode instance.")

        if self.canonical_reference is None:
            return

        if not isinstance(self.canonical_reference, CanonicalEntityReference):
            raise GraphValidationError(
                "canonical_reference must be a CanonicalEntityReference "
                "instance."
            )

        if self.node.node_type != self.canonical_reference.entity_type.value:
            raise GraphContractError(
                "Graph node type must match canonical entity type when a "
                "canonical reference is provided."
            )

        if self.node.node_id != self.canonical_reference.entity_id:
            raise GraphContractError(
                "Graph node identifier must match canonical entity identifier "
                "when a canonical reference is provided."
            )

    @property
    def entity_id(self) -> str:
        """Return the graph entity identifier."""

        return self.node.node_id

    @property
    def entity_type(self) -> str:
        """Return the graph entity type."""

        return self.node.node_type

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "node": self.node.to_mapping(),
        }

        if self.canonical_reference is not None:
            payload["canonical_reference"] = (
                self.canonical_reference.to_mapping()
            )

        return payload
