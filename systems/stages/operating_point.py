"""Stage 04 — establish operating point from requirements / explicit inputs."""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI

from systems.contracts.results import ResultStatus, ValidityInfo, ValidityState, VerificationInfo
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result

__all__ = ("run_operating_point_stage",)


def run_operating_point_stage(
    design: PropulsionDesign,
    *,
    chamber_temperature: float | None = None,
    gamma: float | None = None,
    molecular_weight_kg_per_mol: float | None = None,
) -> object:
    """
    Populate operating point from requirements and optional thermo assumptions.

    Physical quantities use Core Quantity. Assumed gamma/Tc/MW are flagged.
    """

    stage_id = "operating_point"
    op = design.operating_point
    req = design.requirements
    assumptions: list[str] = []

    try:
        if req.target_chamber_pressure is not None:
            op.chamber_pressure = req.target_chamber_pressure
        if req.ambient_pressure is not None:
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
