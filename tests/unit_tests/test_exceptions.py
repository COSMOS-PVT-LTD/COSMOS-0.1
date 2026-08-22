"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.test_exceptions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Verify the shared COSMOS exception hierarchy.

Description:
    Tests inheritance, messages, exception chaining, public exports, and
    documentation for every application-defined exception type.
"""

from __future__ import annotations

# Standard Library
from collections.abc import Iterator

# Third Party
import pytest

# COSMOS Core
from core import exceptions


DOMAIN_EXCEPTIONS = (
    exceptions.ValidationError,
    exceptions.InvalidInputError,
    exceptions.GeometryError,
    exceptions.SolverError,
    exceptions.SolverConvergenceError,
    exceptions.DatabaseError,
    exceptions.CFDError,
    exceptions.GUIError,
)


@pytest.mark.parametrize("exception_type", DOMAIN_EXCEPTIONS)
def test_domain_exceptions_inherit_from_cosmos_error(
    exception_type: type[exceptions.CosmosError],
) -> None:
    """Verify every domain exception is catchable as a COSMOS error."""
    assert issubclass(exception_type, exceptions.CosmosError)
    assert issubclass(exception_type, Exception)


def test_specialized_exceptions_inherit_from_domain_parent() -> None:
    """Verify specialized failures preserve their domain classification."""
    assert issubclass(
        exceptions.InvalidInputError,
        exceptions.ValidationError,
    )
    assert issubclass(
        exceptions.SolverConvergenceError,
        exceptions.SolverError,
    )


@pytest.mark.parametrize("exception_type", DOMAIN_EXCEPTIONS)
def test_exception_message_is_preserved(
    exception_type: type[exceptions.CosmosError],
) -> None:
    """Verify each exception provides a meaningful caller-supplied message."""
    message = "COSMOS operation failed."
    error = exception_type(message)

    assert str(error) == message
    assert error.args == (message,)


def _raise_chained_input_error() -> Iterator[None]:
    """Raise an input error with its original Python exception attached."""
    try:
        float("invalid")
    except ValueError as exc:
        raise exceptions.InvalidInputError(
            "Invalid chamber pressure."
        ) from exc

    yield


def test_exception_chaining_preserves_original_cause() -> None:
    """Verify COSMOS exceptions retain low-level diagnostic context."""
    with pytest.raises(exceptions.InvalidInputError) as captured:
        next(_raise_chained_input_error())

    assert isinstance(captured.value.__cause__, ValueError)
    assert str(captured.value) == "Invalid chamber pressure."


def test_cosmos_error_catches_all_domain_exceptions() -> None:
    """Verify callers can catch all COSMOS failures through the base type."""
    for exception_type in DOMAIN_EXCEPTIONS:
        with pytest.raises(exceptions.CosmosError):
            raise exception_type("Expected test failure.")


def test_public_exports_are_unique_documented_exception_classes() -> None:
    """Verify the public exception API is complete and documented."""
    assert len(exceptions.__all__) == len(set(exceptions.__all__))

    for name in exceptions.__all__:
        exception_type = getattr(exceptions, name)

        assert isinstance(exception_type, type)
        assert issubclass(exception_type, Exception)
        assert exception_type.__doc__
