"""Stage 05 — thermochemistry (CEA interface honest; assumed state partial)."""

from __future__ import annotations

from dataclasses import replace

from core.dimension import TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.quantities import as_si
from physics.thermochemistry.cea_interface import (
    CEA_INTERFACE,
    CeaRequest,
    run_thermochemistry,
)
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import (
    failed_result,
    make_result,
    not_implemented_result,
    stage_guard,
)
from systems.stages.operating_point import (
    _commit_operating_point,
    _validated_chamber_assumptions,
)

__all__ = ("run_thermochemistry_stage",)


@stage_guard("thermochemistry")
def run_thermochemistry_stage(
    design: PropulsionDesign,
    *,
    engine=None,
    assume_chamber_temperature_k: float | None = None,
    assume_gamma: float | None = None,
    assume_molar_mass_kg_per_mol: float | None = None,
    expansion_ratio: float | None = None,
) -> CalculationResult:
    """
    Attempt CEA-backed thermochemistry when an engine is bound.

    Without an engine:
      - If assumed chamber state is provided, record PARTIAL CURRENT with assumptions.
      - Otherwise return NOT_IMPLEMENTED (no fabricated CEA).
    """

    stage_id = "thermochemistry"
    cfg = design.propellant_configuration
    accepted = design.operating_point
    op = replace(accepted)

    try:
        _validated_chamber_assumptions(assume_chamber_temperature_k, assume_gamma, assume_molar_mass_kg_per_mol)
        if assume_chamber_temperature_k is not None:
            op.chamber_temperature = Quantity(float(assume_chamber_temperature_k), SI.get("K"))
            op.chamber_temperature_is_assumption = True
        if assume_gamma is not None:
            op.gamma = float(assume_gamma)
            op.gamma_is_assumption = True
        if assume_molar_mass_kg_per_mol is not None:
            op.molecular_weight = float(assume_molar_mass_kg_per_mol)
        if engine is None:
            _validated_chamber_assumptions(
                None if op.chamber_temperature is None else as_si(op.chamber_temperature, TEMPERATURE, "chamber_temperature"),
                op.gamma, op.molecular_weight,
            )
    except Exception as exc:  # noqa: BLE001 — preserve typed failure, never apply partial assumptions
        result = failed_result(
            calculation_type="thermochemistry.assumed_state" if engine is None else "thermochemistry.cea",
            stage_id=stage_id, exc=exc, design_revision=design.revision,
            model_id="SYS-05.thermochemistry.assumed" if engine is None else CEA_INTERFACE.model_id,
        )
        design.store_stage_result(stage_id, result)
        return result

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
                expansion_ratio=expansion_ratio if expansion_ratio is not None else design.requirements.expansion_ratio,
            )
            if design.thermochemistry_configuration.get("mode") == "nasa_cea" and request.expansion_ratio is None:
                raise InvalidInputError("CEA workbench requires an explicit nozzle expansion ratio > 1.")
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
                model_id=f"{CEA_INTERFACE.model_id}:{thermo.engine_name}",
                model_version=thermo.engine_version,
                inputs={
                    "fuel_id": cfg.fuel_id,
                    "oxidizer_id": cfg.oxidizer_id,
                    "mixture_ratio": cfg.mixture_ratio,
                    "chamber_pressure": op.chamber_pressure.to_canonical_dict(),
                    "engine": thermo.engine_name,
                    "engine_version": thermo.engine_version,
                    "expansion_ratio": request.expansion_ratio,
                    "thermochemistry_configuration": dict(design.thermochemistry_configuration),
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
                    "mole_fractions": dict(thermo.mole_fractions),
                    "rocket_stations": thermo.rocket_stations,
                    "engine_provenance": thermo.provenance,
                },
                assumptions=(*CEA_INTERFACE.assumptions, "Infinite-area adiabatic combustor and ideal equilibrium nozzle; no combustion/loss efficiency correction."),
                warnings=("Validation: NOT_CLAIMED. Solver convergence is not physical engine validation.",
                          *((str(thermo.provenance["reactant_enthalpy_limitation"]),)
                            if "reactant_enthalpy_limitation" in thermo.provenance else ())),
                validity=ValidityInfo(
                    status=ValidityState.VALID,
                    valid_range=CEA_INTERFACE.validity_range,
                ),
                verification=VerificationInfo(status="EXTERNAL_SOLVER_CONVERGED"),
                source=CEA_INTERFACE.source,
                design_revision=design.revision,
            )
            _commit_operating_point(accepted, op)
            design.store_stage_result(stage_id, result)
            design.workflow.invalidate_from(stage_id)
            design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
            design.workflow.results[stage_id].status = ResultStatus.CURRENT
            return result
        except Exception as exc:  # noqa: BLE001
            # Do not leave old chamber values available to a later assumed run.
            op.chamber_temperature = None
            op.gamma = None
            op.molecular_weight = None
            op.characteristic_velocity = None
            op.mass_flow = None
            result = failed_result(
                calculation_type="thermochemistry.cea",
                stage_id=stage_id,
                exc=exc,
                design_revision=design.revision,
                model_id=CEA_INTERFACE.model_id,
                out_of_range=isinstance(exc, OutOfRangeError),
            )
            _commit_operating_point(accepted, op)
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

    if (op.gamma is not None and op.chamber_temperature is not None and op.molecular_weight is not None
            and op.gamma_is_assumption and op.chamber_temperature_is_assumption):
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
        _commit_operating_point(accepted, op)
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result

    if not op.gamma_is_assumption or not op.chamber_temperature_is_assumption:
        op.chamber_temperature = None
        op.gamma = None
        op.molecular_weight = None
        op.characteristic_velocity = None
        op.mass_flow = None
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
    _commit_operating_point(accepted, op)
    design.store_stage_result(stage_id, result)
    return result
