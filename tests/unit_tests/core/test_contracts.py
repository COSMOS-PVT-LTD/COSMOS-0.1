"""Unit tests for core.contracts and core.exceptions hierarchy."""

from __future__ import annotations

import pytest

from core.contracts import ValidationIssue, ValidationResult
from core import exceptions


def test_validation_result_valid_and_invalid() -> None:
    assert ValidationResult.valid().is_valid
    invalid = ValidationResult.invalid(
        ValidationIssue(code="x", message="failed")
    )
    assert not invalid.is_valid
    assert invalid.error_messages == ("failed",)


def test_core_exception_hierarchy() -> None:
    assert issubclass(exceptions.UnitError, exceptions.CoreError)
    assert issubclass(exceptions.UnitError, exceptions.CosmosError)
    assert issubclass(exceptions.DimensionError, exceptions.CoreError)
    assert issubclass(exceptions.SerializationError, exceptions.CoreError)
    assert issubclass(exceptions.CosmosError, exceptions.CoreError)
    assert issubclass(exceptions.InvalidInputError, exceptions.ValidationError)


@pytest.mark.parametrize(
    "exception_type",
    (
        exceptions.UnitError,
        exceptions.DimensionError,
        exceptions.SerializationError,
        exceptions.ContractError,
        exceptions.RegistryError,
        exceptions.ConfigurationError,
    ),
)
def test_core_errors_are_cosmos_errors(
    exception_type: type[exceptions.CosmosError],
) -> None:
    with pytest.raises(exceptions.CosmosError):
        raise exception_type("expected")
