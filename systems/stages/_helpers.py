"""Shared helpers for building stage CalculationResult envelopes."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

from core.exceptions import InvalidInputError
from core.logger import get_logger
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

if TYPE_CHECKING:
    from systems.projects.models import PropulsionDesign

_LOGGER = get_logger(__name__)


def stage_guard(
    stage_id: str,
) -> Callable[[Callable[..., CalculationResult]], Callable[..., CalculationResult]]:
    """Check required inputs before computation; expose all dependency gaps."""

    def decorate(
        function: Callable[..., CalculationResult],
    ) -> Callable[..., CalculationResult]:
        @wraps(function)
        def guarded(design: PropulsionDesign, **kwargs: Any) -> CalculationResult:
            from systems.workflow.readiness import dependency_assessment

            _LOGGER.info("Stage start: %s", stage_id)
            gaps = [
                row
                for row in dependency_assessment(design.workflow, stage_id)
                if row["satisfied"] is False
            ]
            blockers = [row for row in gaps if row["requirement"] == "REQUIRED"]
            if blockers:
                reason = "; ".join(
                    f"{row['stage_id']}={row['status']}" for row in blockers
                )
                result = failed_result(
                    calculation_type=f"workflow.{stage_id}",
                    stage_id=stage_id,
                    exc=InvalidInputError(
                        f"Required dependencies unavailable: {reason}"
                    ),
                    inputs={"dependency_gaps": gaps},
                    design_revision=design.revision,
                )
                design.store_stage_result(stage_id, result)
                return result
            result = function(design, **kwargs)
            if (
                result.validity.status is ValidityState.OUT_OF_RANGE
                and result.status is ResultStatus.CURRENT
            ):
                result.status = ResultStatus.OUT_OF_RANGE
                design.workflow.graph.get(stage_id).status = result.status
                design.workflow.invalidate_from(stage_id)
                design.stamp_derived_slots_stale(
                    (
                        stage_id,
                        *design.workflow.graph.transitive_dependents(
                            stage_id, data_only=True
                        ),
                    )
                )
            if gaps:
                messages = tuple(
                    f"{row['requirement']} dependency {row['stage_id']}={row['status']}: {row['reason']}"
                    for row in gaps
                )
                result.assumptions = (*result.assumptions, *messages)
                result.warnings = (*result.warnings, *messages)
                result.inputs["dependency_gaps"] = gaps
            _LOGGER.info(
                "Stage complete: %s status=%s model=%s",
                stage_id,
                result.status.value,
                result.model_id,
            )
            return result

        return guarded

    return decorate


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
    _LOGGER.info("Model selected: stage=%s model=%s", stage_id, model_id)
    for assumption in assumptions:
        _LOGGER.info("Stage %s assumption: %s", stage_id, assumption)
    for warning in warnings:
        _LOGGER.warning("Stage %s: %s", stage_id, warning)
    for error in errors:
        _LOGGER.error("Stage %s failure: %s", stage_id, error)
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
        validity=validity or ValidityInfo(status=ValidityState.UNKNOWN),
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
    _LOGGER.error(
        "Structured failure: stage=%s model=%s code=%s",
        stage_id,
        model_id,
        type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
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
            status=ValidityState.OUT_OF_RANGE
            if out_of_range
            else ValidityState.UNKNOWN,
            violations=(str(exc),),
        ),
        design_revision=design_revision,
    )
