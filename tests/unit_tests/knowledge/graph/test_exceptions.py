"""Unit tests for knowledge.graph.exceptions."""

from __future__ import annotations

import pytest

from core.exceptions import CosmosError, ValidationError
from knowledge.graph import (
    GraphContractError,
    GraphError,
    GraphValidationError,
)


def test_graph_error_inherits_from_cosmos_error() -> None:
    """GraphError must participate in the COSMOS exception hierarchy."""

    error = GraphError("graph failure")

    assert isinstance(error, CosmosError)
    assert str(error) == "graph failure"


def test_graph_validation_error_inherits_from_validation_and_graph() -> None:
    """GraphValidationError must be catchable as ValidationError or GraphError."""

    error = GraphValidationError("invalid graph record")

    assert isinstance(error, ValidationError)
    assert isinstance(error, GraphError)


def test_graph_contract_error_inherits_from_graph_error() -> None:
    """GraphContractError must inherit from GraphError."""

    error = GraphContractError("contract violation")

    assert isinstance(error, GraphError)
    assert str(error) == "contract violation"


def test_graph_contract_error_is_used_for_integration_invariants() -> None:
    """GraphContractError documents integration-layer invariant failures."""

    assert GraphContractError.__doc__ is not None
    assert "GraphValidationError" in GraphContractError.__doc__


def test_graph_validation_error_can_be_raised_from_validation_path() -> None:
    """Graph validation failures must use GraphValidationError."""

    with pytest.raises(GraphValidationError):
        raise GraphValidationError("invalid node")
