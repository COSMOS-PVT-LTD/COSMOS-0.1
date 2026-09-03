"""
First Systems→Physics calculation path: isentropic stagnation relations.

Proves the architecture without expanding Physics scope.
"""

from __future__ import annotations

from core.exceptions import CosmosError, InvalidInputError
from core.version import COSMOS_VERSION
from physics.compressible_flow.isentropic import (
    ISENTROPIC,
    stagnation_density_ratio,
    stagnation_pressure_ratio,
    stagnation_temperature_ratio,
)
from physics.exceptions import OutOfRangeError, PhysicsError

from systems.contracts.results import (
    CalculationResult,
    ProvenanceInfo,
    ResultStatus,
    ValidationInfo,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign

__all__ = ("evaluate_isentropic_stagnation",)


def evaluate_isentropic_stagnation(
    design: PropulsionDesign,
    *,
    mach: float,
    gamma: float | None = None,
) -> CalculationResult:
    """
    Run PHYS-004 isentropic stagnation via Systems and store on the design.

    Gamma may come from the operating point when present; otherwise it must be
    supplied explicitly and is recorded as an assumption if the OP marks it so.
    """

    stage_id = "nozzle"
    g = gamma if gamma is not None else design.operating_point.gamma
    if g is None:
        raise InvalidInputError(
            "gamma is required (supply explicitly or set operating_point.gamma)."
        )

    assumptions: list[str] = list(ISENTROPIC.assumptions)
    if design.operating_point.gamma_is_assumption or gamma is not None:
        assumptions.append(f"gamma = {g} supplied as analysis input / assumption.")

    try:
        t_ratio = stagnation_temperature_ratio(mach, g)
        p_ratio = stagnation_pressure_ratio(mach, g)
        rho_ratio = stagnation_density_ratio(mach, g)
    except (InvalidInputError, OutOfRangeError, PhysicsError, CosmosError) as exc:
        result = CalculationResult(
            calculation_type="compressible.isentropic",
            status=(
                ResultStatus.OUT_OF_RANGE
                if isinstance(exc, OutOfRangeError)
                else ResultStatus.FAILED
            ),
            model_id=ISENTROPIC.model_id,
            model_version=ISENTROPIC.version,
            inputs={"mach": {"value": mach, "unit": "1"}, "gamma": {"value": g, "unit": "1"}},
            assumptions=tuple(assumptions),
            errors=(
                {
                    "code": type(exc).__name__,
                    "message": str(exc),
                    "stage": stage_id,
                    "model": ISENTROPIC.model_id,
                },
            ),
            validity=ValidityInfo(
                status=ValidityState.OUT_OF_RANGE
                if isinstance(exc, OutOfRangeError)
                else ValidityState.UNKNOWN,
                valid_range=ISENTROPIC.validity_range,
                violations=(str(exc),),
            ),
            verification=VerificationInfo(status=ISENTROPIC.verification_status),
            validation=ValidationInfo(status="NOT_CLAIMED"),
            provenance=ProvenanceInfo(
                source=ISENTROPIC.source,
                model=ISENTROPIC.model_id,
                version=ISENTROPIC.version,
                software_version=COSMOS_VERSION,
                calculation_revision=design.revision,
            ),
            design_revision=design.revision,
            stage_id=stage_id,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        return result

    result = CalculationResult(
        calculation_type="compressible.isentropic",
        status=ResultStatus.CURRENT,
        model_id=ISENTROPIC.model_id,
        model_version=ISENTROPIC.version,
        inputs={"mach": {"value": mach, "unit": "1"}, "gamma": {"value": g, "unit": "1"}},
        outputs={
            "T0_over_T": {"value": t_ratio, "unit": "1"},
            "p0_over_p": {"value": p_ratio, "unit": "1"},
            "rho0_over_rho": {"value": rho_ratio, "unit": "1"},
        },
        assumptions=tuple(assumptions),
        warnings=(),
        validity=ValidityInfo(
            status=ValidityState.VALID,
            checks=("mach_and_gamma_accepted_by_physics",),
            valid_range=ISENTROPIC.validity_range,
        ),
        verification=VerificationInfo(
            status="PASS",
            reference=ISENTROPIC.verification_status,
        ),
        validation=ValidationInfo(status="NOT_CLAIMED"),
        provenance=ProvenanceInfo(
            source=ISENTROPIC.source,
            model=ISENTROPIC.model_id,
            version=ISENTROPIC.version,
            software_version=COSMOS_VERSION,
            calculation_revision=design.revision,
        ),
        design_revision=design.revision,
        stage_id=stage_id,
    )
    design.store_stage_result(stage_id, result)
    # Fresh nozzle result invalidates downstream summaries.
    design.workflow.invalidate_from(stage_id)
    # Re-assert nozzle itself is CURRENT after invalidation of dependents only.
    design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
    design.workflow.results[stage_id].status = ResultStatus.CURRENT
    return result
