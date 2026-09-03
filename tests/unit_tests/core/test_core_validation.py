"""Unit tests for core validation helpers and physical constants."""

from __future__ import annotations

import pytest

from core.constants import G0, SPEED_OF_LIGHT
from core.exceptions import InvalidInputError
from core.physical_constant import CODATA_PHYSICAL_CONSTANTS
from core.validation import (
    collect_validation,
    validate_finite,
    validate_mapping_keys,
    validate_not_none,
    validate_type,
)
from core.contracts import ValidationResult


def test_validate_finite_rejects_nan() -> None:
    with pytest.raises(InvalidInputError):
        validate_finite(float("nan"), "value")


def test_validate_not_none() -> None:
    assert validate_not_none(3, "value") == 3
    with pytest.raises(InvalidInputError):
        validate_not_none(None, "value")


def test_validate_type() -> None:
    assert validate_type("x", str, "value") == "x"
    with pytest.raises(InvalidInputError):
        validate_type(1, str, "value")


def test_validate_mapping_keys() -> None:
    data = {"a": 1}
    assert validate_mapping_keys(data, ("a",), "payload") == data
    with pytest.raises(InvalidInputError):
        validate_mapping_keys(data, ("b",), "payload")


def test_collect_validation_merges_issues() -> None:
    from core.contracts import ValidationIssue

    merged = collect_validation(
        ValidationResult.valid(),
        ValidationResult.invalid(
            ValidationIssue(code="a", message="first"),
            ValidationIssue(code="b", message="second"),
        ),
    )
    assert not merged.is_valid
    assert len(merged.issues) == 2


def test_codata_constants_include_speed_of_light() -> None:
    symbols = {constant.symbol for constant in CODATA_PHYSICAL_CONSTANTS}
    assert "c" in symbols


def test_standard_gravity_value() -> None:
    gravity = next(
        constant
        for constant in CODATA_PHYSICAL_CONSTANTS
        if constant.symbol == "g_0"
    )
    assert gravity.quantity.to_si() == G0


def test_speed_of_light_exact_si_value() -> None:
    light = next(
        constant
        for constant in CODATA_PHYSICAL_CONSTANTS
        if constant.symbol == "c"
    )
    assert light.quantity.to_si() == SPEED_OF_LIGHT
