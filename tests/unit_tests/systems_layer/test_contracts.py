"""Unit tests for Systems calculation-result contract."""

from __future__ import annotations

from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidationInfo,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
    is_current_displayable,
)


def test_only_current_is_displayable() -> None:
    assert is_current_displayable(ResultStatus.CURRENT) is True
    for status in ResultStatus:
        if status is ResultStatus.CURRENT:
            continue
        assert is_current_displayable(status) is False


def test_mark_stale_preserves_history_semantics() -> None:
    result = CalculationResult(
        calculation_type="compressible.isentropic",
        status=ResultStatus.CURRENT,
    )
    result.mark_stale()
    assert result.status is ResultStatus.STALE
    assert is_current_displayable(result.status) is False


def test_result_round_trip_preserves_vv_separation() -> None:
    result = CalculationResult(
        calculation_type="compressible.isentropic",
        status=ResultStatus.CURRENT,
        model_id="PHYS-004.isentropic.stagnation",
        model_version="0.1.0",
        verification=VerificationInfo(status="PASS", reference="Anderson"),
        validation=ValidationInfo(status="NOT_CLAIMED"),
        validity=ValidityInfo(status=ValidityState.VALID, valid_range="M>=0"),
    )
    restored = CalculationResult.from_canonical_dict(result.to_canonical_dict())
    assert restored.verification.status == "PASS"
    assert restored.validation.status == "NOT_CLAIMED"
    assert restored.validity.status is ValidityState.VALID
    assert restored.model_id == "PHYS-004.isentropic.stagnation"
