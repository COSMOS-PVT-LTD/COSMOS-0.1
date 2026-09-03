"""Stage 05 — thermochemistry (CEA interface honest; assumed state partial)."""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.thermochemistry.cea_interface import (
    CEA_INTERFACE,
    CeaRequest,
    run_thermochemistry,
)

from systems.contracts.results import (
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, not_implemented_result

__all__ = ("run_thermochemistry_stage",)


def run_thermochemistry_stage(
    design: PropulsionDesign,
    *,
    engine=None,
    assume_chamber_temperature_k: float | None = None,
    assume_gamma: float | None = None,
    assume_molar_mass_kg_per_mol: float | None = None,
) -> object:
    """
    Attempt CEA-backed thermochemistry when an engine is bound.

    Without an engine:
      - If assumed chamber state is provided, record PARTIAL CURRENT with assumptions.
      - Otherwise return NOT_IMPLEMENTED (no fabricated CEA).
    """

    stage_id = "thermochemistry"
    cfg = design.propellant_configuration
    op = design.operating_point

    if assume_chamber_temperature_k is not None:
        op.chamber_temperature = Quantity(float(assume_chamber_temperature_k), SI.get("K"))
        op.chamber_temperature_is_assumption = True
    if assume_gamma is not None:
        op.gamma = float(assume_gamma)
        op.gamma_is_assumption = True
    if assume_molar_mass_kg_per_mol is not None:
        op.molecular_weight = float(assume_molar_mass_kg_per_mol)

    # Prefer external engine when provided.
    if engine is not None:
        try:
            if not cfg.fuel_id or not cfg.oxidizer_id or cfg.mixture_ratio is None:
                raise InvalidInputError(
                    "CEA path requires fuel_id, oxidizer_id, and mixture_ratio."
                )
            if op.chamber_pressure is None:
                raise InvalidInputError("CEA path requires chamber_pressure on operating point.")
            request = CeaRequest(
                fuel_id=cfg.fuel_id,
                oxidizer_id=cfg.oxidizer_id,
                mixture_ratio=float(cfg.mixture_ratio),
                chamber_pressure=op.chamber_pressure,
            )
            thermo = run_thermochemistry(request, engine=engine)
            op.chamber_temperature = thermo.chamber_temperature
            op.chamber_temperature_is_assumption = False
            op.gamma = float(thermo.gamma)
            op.gamma_is_assumption = False
            op.molecular_weight = float(thermo.molar_mass.to_si())
            if thermo.characteristic_velocity is not None:
                op.characteristic_velocity = thermo.characteristic_velocity
            result = make_result(
                calculation_type="thermochemistry.cea",
                stage_id=stage_id,
                status=ResultStatus.CURRENT,
                model_id=CEA_INTERFACE.model_id,
                model_version=CEA_INTERFACE.version,
                inputs={
                    "fuel_id": cfg.fuel_id,
                    "oxidizer_id": cfg.oxidizer_id,
                    "mixture_ratio": cfg.mixture_ratio,
                    "chamber_pressure": op.chamber_pressure.to_canonical_dict(),
                    "engine": thermo.engine_name,
                },
                outputs={
                    "chamber_temperature": thermo.chamber_temperature.to_canonical_dict(),
                    "gamma": {"value": thermo.gamma, "unit": "1"},
                    "molar_mass": thermo.molar_mass.to_canonical_dict(),
                    "cstar": (
                        None
                        if thermo.characteristic_velocity is None
                        else thermo.characteristic_velocity.to_canonical_dict()
                    ),
                },
                assumptions=tuple(CEA_INTERFACE.assumptions),
                validity=ValidityInfo(
                    status=ValidityState.VALID,
                    valid_range=CEA_INTERFACE.validity_range,
                ),
                verification=VerificationInfo(status=CEA_INTERFACE.verification_status),
                source=CEA_INTERFACE.source,
                design_revision=design.revision,
            )
            design.store_stage_result(stage_id, result)
            design.workflow.invalidate_from(stage_id)
            design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
            design.workflow.results[stage_id].status = ResultStatus.CURRENT
            return result
        except Exception as exc:  # noqa: BLE001
            result = failed_result(
                calculation_type="thermochemistry.cea",
                stage_id=stage_id,
                exc=exc,
                design_revision=design.revision,
                model_id=CEA_INTERFACE.model_id,
                out_of_range=isinstance(exc, OutOfRangeError),
            )
            design.store_stage_result(stage_id, result)
            return result

    # No engine: attempt unbound CEA to document the fail-closed message, then
    # fall back to assumed chamber state if provided.
    cea_message = ""
    try:
        if cfg.fuel_id and cfg.oxidizer_id and cfg.mixture_ratio is not None and op.chamber_pressure:
            run_thermochemistry(
                CeaRequest(
                    fuel_id=cfg.fuel_id,
                    oxidizer_id=cfg.oxidizer_id,
                    mixture_ratio=float(cfg.mixture_ratio),
                    chamber_pressure=op.chamber_pressure,
                ),
                engine=None,
            )
    except InsufficientDataError as exc:
        cea_message = str(exc)

    if op.gamma is not None and op.chamber_temperature is not None and op.molecular_weight is not None:
        assumptions = [
            "Chamber state is ASSUMED — CEA engine not bound.",
            f"gamma = {op.gamma}",
            f"Tc = {op.chamber_temperature.to_si()} K",
            f"MW = {op.molecular_weight} kg/mol",
        ]
        if cea_message:
            assumptions.append(f"CEA unavailable: {cea_message}")
        result = make_result(
            calculation_type="thermochemistry.assumed_state",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-05.thermochemistry.assumed",
            model_version="0.1.0",
            inputs=op.to_canonical_dict(),
            outputs={
                "chamber_temperature": op.chamber_temperature.to_canonical_dict(),
                "gamma": {"value": op.gamma, "unit": "1"},
                "molar_mass": {"value": op.molecular_weight, "unit": "kg/mol"},
                "cea_status": {"value": "NOT_BOUND", "unit": "1"},
            },
            assumptions=tuple(assumptions),
            warnings=("Validation: NOT_CLAIMED. Assumed thermo is not CEA equilibrium.",),
            validity=ValidityInfo(status=ValidityState.UNKNOWN),
            verification=VerificationInfo(status="ASSUMED_INPUT"),
            source="User/analysis assumption (no CEA execution)",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result

    result = not_implemented_result(
        calculation_type="thermochemistry.cea",
        stage_id=stage_id,
        reason=cea_message
        or (
            "No external thermochemistry engine bound and no assumed chamber "
            "state (gamma, Tc, MW) provided."
        ),
        design_revision=design.revision,
        model_id=CEA_INTERFACE.model_id,
        inputs={
            "fuel_id": cfg.fuel_id,
            "oxidizer_id": cfg.oxidizer_id,
            "mixture_ratio": cfg.mixture_ratio,
        },
    )
    design.store_stage_result(stage_id, result)
    return result
