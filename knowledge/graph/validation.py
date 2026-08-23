"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.validation

Purpose:
    Graph record validation for constructed knowledge graphs.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.contracts import GraphNode, ImmutableGraphRecord
from knowledge.graph.exceptions import GraphValidationError
from knowledge.graph.lifecycle import GraphLifecycleState

__all__ = (
    "GraphRecordValidationIssue",
    "GraphRecordValidationReport",
    "GraphRecordValidator",
)


_REQUIRED_NODE_PROPERTIES = frozenset(
    {
        "lifecycle_state",
        "document_id",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphRecordValidationIssue:
    """Single validation issue discovered in a graph record."""

    code: str
    message: str
    node_id: str | None = None
    relationship_id: str | None = None

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }

        if self.node_id is not None:
            payload["node_id"] = self.node_id
        if self.relationship_id is not None:
            payload["relationship_id"] = self.relationship_id

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphRecordValidationReport:
    """Validation report for a graph record."""

    issues: tuple[GraphRecordValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return True when no validation issues were found."""

        return not self.issues

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_mapping() for issue in self.issues],
        }


class GraphRecordValidator:
    """
    Validate graph records produced by the construction pipeline.

    Validation is structural and provenance-oriented; it does not perform
    engineering approval.
    """

    def validate(self, record: ImmutableGraphRecord) -> GraphRecordValidationReport:
        """Validate a graph record and return a structured report."""

        if not isinstance(record, ImmutableGraphRecord):
            raise GraphValidationError(
                "record must be an ImmutableGraphRecord instance."
            )

        issues: list[GraphRecordValidationIssue] = []

        node_ids = {node.node_id for node in record.nodes}

        for node in record.nodes:
            issues.extend(self._validate_node(node))

        for relationship in record.relationships:
            if relationship.source_node_id not in node_ids:
                issues.append(
                    GraphRecordValidationIssue(
                        code="missing_source_endpoint",
                        message="Relationship source endpoint is missing.",
                        relationship_id=relationship.relationship_id,
                    )
                )

            if relationship.target_node_id not in node_ids:
                issues.append(
                    GraphRecordValidationIssue(
                        code="missing_target_endpoint",
                        message="Relationship target endpoint is missing.",
                        relationship_id=relationship.relationship_id,
                    )
                )

        return GraphRecordValidationReport(issues=tuple(issues))

    def validate_or_raise(self, record: ImmutableGraphRecord) -> None:
        """Validate a graph record and raise when invalid."""

        report = self.validate(record)

        if not report.is_valid:
            first_issue = report.issues[0]
            raise GraphValidationError(first_issue.message)

    def _validate_node(self, node: GraphNode) -> list[GraphRecordValidationIssue]:
        issues: list[GraphRecordValidationIssue] = []

        for property_name in _REQUIRED_NODE_PROPERTIES:
            if property_name not in node.properties:
                issues.append(
                    GraphRecordValidationIssue(
                        code="missing_node_property",
                        message=(
                            f"Node is missing required property "
                            f"'{property_name}'."
                        ),
                        node_id=node.node_id,
                    )
                )

        lifecycle_value = node.properties.get("lifecycle_state")

        if lifecycle_value is not None:
            valid_states = {
                state.value for state in GraphLifecycleState
            }

            if str(lifecycle_value) not in valid_states:
                issues.append(
                    GraphRecordValidationIssue(
                        code="invalid_lifecycle_state",
                        message="Node lifecycle_state is not recognized.",
                        node_id=node.node_id,
                    )
                )
            elif str(lifecycle_value) == GraphLifecycleState.APPROVED.value:
                issues.append(
                    GraphRecordValidationIssue(
                        code="premature_approval",
                        message=(
                            "Constructed graph nodes must not be in "
                            "APPROVED state."
                        ),
                        node_id=node.node_id,
                    )
                )

        conflict_visibility = node.properties.get("conflict_visibility")

        if conflict_visibility == "CONFIRMED_CONFLICT":
            issues.append(
                GraphRecordValidationIssue(
                    code="confirmed_conflict",
                    message="Node participates in a confirmed conflict.",
                    node_id=node.node_id,
                )
            )

        return issues
