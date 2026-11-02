"""Stage 04 — establish operating point from requirements / explicit inputs."""

from __future__ import annotations

from dataclasses import fields, replace

from core.dimension import TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive
from physics.quantities import as_si, require_gamma
from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.operating_point.models import OperatingPoint
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result, stage_guard

__all__ = ("run_operating_point_stage",)


def _validated_chamber_assumptions(
    temperature_k: float | None,
    gamma: float | None,
    molar_mass_kg_per_mol: float | None,
) -> tuple[float | None, float | None, float | None]:
    """Validate all supplied/effective assumptions before accepting any of them."""
    for name, value in (("chamber_temperature_k", temperature_k), ("gamma", gamma),
                        ("molar_mass_kg_per_mol", molar_mass_kg_per_mol)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise InvalidInputError(f"{name} must be a real number.")
    return (
        None if temperature_k is None else validate_positive(temperature_k, "chamber_temperature_k"),
        None if gamma is None else require_gamma(gamma),
        None if molar_mass_kg_per_mol is None else validate_positive(molar_mass_kg_per_mol, "molar_mass_kg_per_mol"),
    )


def _commit_operating_point(target: OperatingPoint, candidate: OperatingPoint) -> None:
    """Commit a checked candidate without changing the public aggregate identity."""
    for item in fields(target):
        setattr(target, item.name, getattr(candidate, item.name))


@stage_guard("operating_point")
def run_operating_point_stage(
    design: PropulsionDesign,
    *,
    chamber_temperature: float | None = None,
    gamma: float | None = None,
    molecular_weight_kg_per_mol: float | None = None,
) -> CalculationResult:
    """
    Populate operating point from requirements and optional thermo assumptions.

    Physical quantities use Core Quantity. Assumed gamma/Tc/MW are flagged.
    """

    stage_id = "operating_point"
    accepted = design.operating_point
    op = replace(accepted)
    req = design.requirements
    assumptions: list[str] = []

    try:
        # Validate the whole effective assumed state first. A later bad gamma/MW
        # must not leave an earlier valid temperature applied to the live design.
        _validated_chamber_assumptions(
            chamber_temperature if chamber_temperature is not None else
            None if op.chamber_temperature is None else as_si(op.chamber_temperature, TEMPERATURE, "chamber_temperature"),
            gamma if gamma is not None else op.gamma,
            molecular_weight_kg_per_mol if molecular_weight_kg_per_mol is not None else op.molecular_weight,
        )
        if req.target_chamber_pressure is not None:
            op.chamber_pressure = req.target_chamber_pressure
        op.ambient_pressure = req.ambient_pressure
        if req.ambient_temperature is not None:
            op.ambient_temperature = req.ambient_temperature
        if req.mixture_ratio is not None:
            op.mixture_ratio = float(req.mixture_ratio)
        elif design.propellant_configuration.mixture_ratio is not None:
            op.mixture_ratio = float(design.propellant_configuration.mixture_ratio)

        if chamber_temperature is not None:
            op.chamber_temperature = Quantity(float(chamber_temperature), SI.get("K"))
            op.chamber_temperature_is_assumption = True
            assumptions.append(f"chamber_temperature = {chamber_temperature} K (assumption).")
        if gamma is not None:
            op.gamma = float(gamma)
            op.gamma_is_assumption = True
            assumptions.append(f"gamma = {gamma} (assumption).")
        if molecular_weight_kg_per_mol is not None:
            op.molecular_weight = float(molecular_weight_kg_per_mol)
            assumptions.append(
                f"molecular_weight = {molecular_weight_kg_per_mol} kg/mol (assumption)."
            )

        if op.chamber_pressure is None:
            raise InvalidInputError(
                "operating point requires chamber_pressure "
                "(set requirements.target_chamber_pressure)."
            )

        result = make_result(
            calculation_type="workflow.operating_point",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-04.operating_point.establish",
            model_version="0.1.0",
            inputs={
                "requirements": req.to_canonical_dict(),
                "overrides": {
                    "chamber_temperature": chamber_temperature,
                    "gamma": gamma,
                    "molecular_weight_kg_per_mol": molecular_weight_kg_per_mol,
                },
            },
            outputs=op.to_canonical_dict(),
            assumptions=tuple(assumptions),
            warnings=(
                ()
                if op.gamma is not None
                else ("gamma unset — thermochemistry or explicit gamma required for performance.",)
            ),
            validity=ValidityInfo(status=ValidityState.NOT_APPLICABLE),
            verification=VerificationInfo(status="PASS", reference="operating point capture"),
            source="COSMOS Systems operating-point stage",
            design_revision=design.revision,
        )
        _commit_operating_point(accepted, op)
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001
        result = failed_result(
            calculation_type="workflow.operating_point",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result
