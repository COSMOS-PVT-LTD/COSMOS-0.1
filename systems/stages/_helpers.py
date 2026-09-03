"""Shared helpers for building stage CalculationResult envelopes."""

from __future__ import annotations

from typing import Any

from core.version import COSMOS_VERSION

from systems.contracts.results import (
    CalculationResult,
    ProvenanceInfo,
    ResultStatus,
    ValidationInfo,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)

__all__ = ("failed_result", "make_result", "not_implemented_result")


def make_result(
    *,
    calculation_type: str,
    stage_id: str,
    status: ResultStatus,
    model_id: str | None = None,
    model_version: str | None = None,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    assumptions: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    errors: tuple[dict[str, str], ...] = (),
    validity: ValidityInfo | None = None,
    verification: VerificationInfo | None = None,
    validation: ValidationInfo | None = None,
    source: str | None = None,
    design_revision: int = 0,
) -> CalculationResult:
    return CalculationResult(
        calculation_type=calculation_type,
        status=status,
        model_id=model_id,
        model_version=model_version,
        inputs=dict(inputs or {}),
        outputs=dict(outputs or {}),
        assumptions=assumptions,
        warnings=warnings,
        errors=errors,
        validity=validity
        or ValidityInfo(status=ValidityState.UNKNOWN),
        verification=verification or VerificationInfo(status="UNKNOWN"),
        validation=validation or ValidationInfo(status="NOT_CLAIMED"),
        provenance=ProvenanceInfo(
            source=source,
            model=model_id,
            version=model_version,
            software_version=COSMOS_VERSION,
            calculation_revision=design_revision,
        ),
        design_revision=design_revision,
        stage_id=stage_id,
    )


def not_implemented_result(
    *,
    calculation_type: str,
    stage_id: str,
    reason: str,
    design_revision: int = 0,
    model_id: str | None = None,
    inputs: dict[str, Any] | None = None,
) -> CalculationResult:
    return make_result(
        calculation_type=calculation_type,
        stage_id=stage_id,
        status=ResultStatus.NOT_IMPLEMENTED,
        model_id=model_id,
        inputs=inputs,
        warnings=(reason,),
        errors=({"code": "NOT_IMPLEMENTED", "message": reason, "stage": stage_id},),
        design_revision=design_revision,
    )


def failed_result(
    *,
    calculation_type: str,
    stage_id: str,
    exc: BaseException,
    design_revision: int = 0,
    model_id: str | None = None,
    inputs: dict[str, Any] | None = None,
    out_of_range: bool = False,
) -> CalculationResult:
    return make_result(
        calculation_type=calculation_type,
        stage_id=stage_id,
        status=ResultStatus.OUT_OF_RANGE if out_of_range else ResultStatus.FAILED,
        model_id=model_id,
        inputs=inputs,
        errors=(
            {
                "code": type(exc).__name__,
                "message": str(exc),
                "stage": stage_id,
                "model": model_id or "",
            },
        ),
        validity=ValidityInfo(
            status=ValidityState.OUT_OF_RANGE if out_of_range else ValidityState.UNKNOWN,
            violations=(str(exc),),
        ),
        design_revision=design_revision,
    )
