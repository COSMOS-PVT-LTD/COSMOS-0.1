"""Stage 01 — commit / validate design requirements."""

from __future__ import annotations

from systems.contracts.results import ResultStatus, ValidityInfo, ValidityState, VerificationInfo
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import failed_result, make_result

__all__ = ("run_requirements_stage",)


def run_requirements_stage(design: PropulsionDesign) -> object:
    """
    Capture requirements into a CURRENT stage result.

    Does not invent missing values. Warns when critical fields are absent.
    """

    stage_id = "requirements"
    req = design.requirements
    try:
        inputs: dict[str, object] = req.to_canonical_dict()
        warnings: list[str] = []
        if req.target_chamber_pressure is None:
            warnings.append("target_chamber_pressure is unset.")
        if req.mixture_ratio is None:
            warnings.append("mixture_ratio is unset.")
        if req.propellant_selection is None and req.cycle_type is None:
            warnings.append("No propellant_selection or cycle_type recorded.")

        result = make_result(
            calculation_type="workflow.requirements",
            stage_id=stage_id,
            status=ResultStatus.CURRENT,
            model_id="SYS-01.requirements.capture",
            model_version="0.1.0",
            inputs=inputs,
            outputs={
                "fields_set": {
                    "value": sum(1 for v in inputs.values() if v is not None),
                    "unit": "1",
                }
            },
            assumptions=(),
            warnings=tuple(warnings),
            validity=ValidityInfo(status=ValidityState.NOT_APPLICABLE),
            verification=VerificationInfo(status="PASS", reference="requirements capture"),
            source="COSMOS Systems requirements stage",
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        design.workflow.invalidate_from(stage_id)
        design.workflow.graph.get(stage_id).status = ResultStatus.CURRENT
        design.workflow.results[stage_id].status = ResultStatus.CURRENT
        return result
    except Exception as exc:  # noqa: BLE001 — mapped into typed envelope
        result = failed_result(
            calculation_type="workflow.requirements",
            stage_id=stage_id,
            exc=exc,
            design_revision=design.revision,
        )
        design.store_stage_result(stage_id, result)
        return result
