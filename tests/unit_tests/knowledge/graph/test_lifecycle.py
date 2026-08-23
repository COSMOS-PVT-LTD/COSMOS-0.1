"""Unit tests for knowledge.graph.lifecycle."""

from __future__ import annotations

import pytest

from knowledge.graph import GraphValidationError
from knowledge.graph.lifecycle import (
    GraphLifecycleMetadata,
    GraphLifecycleState,
    GraphLifecycleTransitionError,
    allowed_lifecycle_targets,
    is_terminal_lifecycle_state,
    transition_lifecycle_state,
)


def test_valid_lifecycle_transition_extracted_to_candidate() -> None:
    """Extracted records may become candidates."""

    current = GraphLifecycleMetadata(state=GraphLifecycleState.EXTRACTED)

    updated = transition_lifecycle_state(
        current,
        GraphLifecycleState.CANDIDATE,
    )

    assert updated.state is GraphLifecycleState.CANDIDATE
    assert updated.record_version == 2


def test_invalid_lifecycle_transition_is_rejected() -> None:
    """Disallowed transitions must raise GraphLifecycleTransitionError."""

    current = GraphLifecycleMetadata(state=GraphLifecycleState.EXTRACTED)

    with pytest.raises(GraphLifecycleTransitionError):
        transition_lifecycle_state(current, GraphLifecycleState.APPROVED)


def test_terminal_states_have_no_outgoing_transitions() -> None:
    """Rejected and deprecated states must be terminal."""

    assert is_terminal_lifecycle_state(GraphLifecycleState.REJECTED)
    assert is_terminal_lifecycle_state(GraphLifecycleState.DEPRECATED)
    assert allowed_lifecycle_targets(GraphLifecycleState.REJECTED) == frozenset()


def test_reviewed_may_transition_to_approved_or_rejected() -> None:
    """Reviewed records may be approved, rejected, or deprecated."""

    targets = allowed_lifecycle_targets(GraphLifecycleState.REVIEWED)

    assert GraphLifecycleState.APPROVED in targets
    assert GraphLifecycleState.REJECTED in targets
    assert GraphLifecycleState.DEPRECATED in targets


def test_repeated_transition_increments_record_version() -> None:
    """Each valid transition must increment record_version."""

    current = GraphLifecycleMetadata(state=GraphLifecycleState.EXTRACTED)
    candidate = transition_lifecycle_state(
        current,
        GraphLifecycleState.CANDIDATE,
    )
    reviewed = transition_lifecycle_state(
        candidate,
        GraphLifecycleState.REVIEWED,
    )

    assert reviewed.record_version == 3


def test_graph_lifecycle_metadata_rejects_invalid_version() -> None:
    """Lifecycle metadata must use positive integer versions."""

    with pytest.raises(GraphValidationError):
        GraphLifecycleMetadata(
            state=GraphLifecycleState.EXTRACTED,
            record_version=0,
        )
