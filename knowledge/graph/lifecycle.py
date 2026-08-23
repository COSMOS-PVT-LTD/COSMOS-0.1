"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.lifecycle

Purpose:
    Controlled lifecycle semantics for graph records and assertions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.exceptions import GraphValidationError

__all__ = (
    "GraphLifecycleMetadata",
    "GraphLifecycleState",
    "GraphLifecycleTransitionError",
    "allowed_lifecycle_targets",
    "is_terminal_lifecycle_state",
    "transition_lifecycle_state",
)


class GraphLifecycleState(Enum):
    """
    Lifecycle states for graph records and extracted assertions.

    Vocabulary follows KG-004 batch requirements and remains distinct from
    canonical document approval enums in ``knowledge.models.document``.

    This enum models the graph-record approval subset used by KG-004. It is
    not the full end-to-end knowledge pipeline vocabulary in KG spec §17
    (``UNPROCESSED`` through ``APPROVED`` plus ingestion states). Downstream
    batches may map between pipeline states and these graph-record states.
    """

    EXTRACTED = "EXTRACTED"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"


_TERMINAL_STATES: frozenset[GraphLifecycleState] = frozenset(
    {
        GraphLifecycleState.REJECTED,
        GraphLifecycleState.DEPRECATED,
    }
)


_VALID_TRANSITIONS: dict[
    GraphLifecycleState,
    frozenset[GraphLifecycleState],
] = {
    GraphLifecycleState.EXTRACTED: frozenset(
        {
            GraphLifecycleState.CANDIDATE,
            GraphLifecycleState.REJECTED,
        }
    ),
    GraphLifecycleState.CANDIDATE: frozenset(
        {
            GraphLifecycleState.REVIEWED,
            GraphLifecycleState.REJECTED,
        }
    ),
    GraphLifecycleState.REVIEWED: frozenset(
        {
            GraphLifecycleState.APPROVED,
            GraphLifecycleState.REJECTED,
            GraphLifecycleState.DEPRECATED,
        }
    ),
    GraphLifecycleState.APPROVED: frozenset(
        {
            GraphLifecycleState.DEPRECATED,
        }
    ),
    GraphLifecycleState.REJECTED: frozenset(),
    GraphLifecycleState.DEPRECATED: frozenset(),
}


class GraphLifecycleTransitionError(GraphValidationError):
    """Indicate that a lifecycle transition is not permitted."""


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphLifecycleMetadata:
    """
    Immutable lifecycle metadata for a graph record.

    ``record_version`` is an explicit integer revision and does not use wall
    clock time for identity.
    """

    state: GraphLifecycleState
    record_version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.state, GraphLifecycleState):
            raise GraphValidationError(
                "state must be a GraphLifecycleState value."
            )

        if not isinstance(self.record_version, int) or isinstance(
            self.record_version,
            bool,
        ):
            raise GraphValidationError(
                "record_version must be an integer."
            )

        if self.record_version <= 0:
            raise GraphValidationError(
                "record_version must be a positive integer."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "state": self.state.value,
            "record_version": self.record_version,
        }


def is_terminal_lifecycle_state(state: GraphLifecycleState) -> bool:
    """Return True when no further transitions are permitted."""

    return state in _TERMINAL_STATES


def allowed_lifecycle_targets(
    state: GraphLifecycleState,
) -> frozenset[GraphLifecycleState]:
    """Return the valid target states for a lifecycle state."""

    return _VALID_TRANSITIONS.get(state, frozenset())


def transition_lifecycle_state(
    current: GraphLifecycleMetadata,
    target_state: GraphLifecycleState,
) -> GraphLifecycleMetadata:
    """
    Return a new lifecycle metadata object after a valid transition.

    Raises
    ------
    GraphLifecycleTransitionError
        If the transition is not permitted.
    """

    if not isinstance(target_state, GraphLifecycleState):
        raise GraphValidationError(
            "target_state must be a GraphLifecycleState value."
        )

    allowed_targets = allowed_lifecycle_targets(current.state)

    if target_state not in allowed_targets:
        raise GraphLifecycleTransitionError(
            f"Transition from {current.state.value} to "
            f"{target_state.value} is not permitted."
        )

    return GraphLifecycleMetadata(
        state=target_state,
        record_version=current.record_version + 1,
    )
