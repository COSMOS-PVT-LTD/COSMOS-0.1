"""Stage 14 — aggregate CURRENT stage outputs into a performance summary."""

from __future__ import annotations

from systems.contracts.results import (
    ResultStatus,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import make_result

__all__ = ("run_performance_summary_stage",)

# Keys preferred in the engineering summary (when present on CURRENT results).
_SUMMARY_KEYS = (
    "thrust",
    "specific_impulse",
    "thrust_coefficient",
    "mass_flow",
    "exit_mach",
    "exit_pressure",
    "exit_velocity",
    "cstar",
    "chamber_volume",
    "chamber_diameter",
    "chamber_length",
    "throat_diameter",
    "h",
    "Nu",
    "hoop_stress",
    "longitudinal_stress",
    "yield_strength",
    "hoop_over_yield",
    "material_id",
)


def run_performance_summary_stage(design: PropulsionDesign) -> object:
    """
    Consolidate CURRENT workflow results. Never promotes STALE as current.

    Unavailable / not-implemented stages are listed honestly, not fabricated.
    """

    stage_id = "performance_summary"
    consolidated: dict[str, object] = {}
    by_stage: dict[str, object] = {}
    assumptions: list[str] = []
    warnings: list[str] = []
    current_count = 0
    not_implemented: list[str] = []
    stale_or_failed: list[str] = []

    for sid, node in sorted(design.workflow.graph.nodes.items()):
        stored = design.workflow.results.get(sid)
        current = design.workflow.current_result(sid)
        if current is not None:
            current_count += 1
            by_stage[sid] = {
                "status": current.status.value,
                "model_id": current.model_id,
                "model_version": current.model_version,
                "outputs": dict(current.outputs),
                "result_id": current.result_id,
            }
            for key in _SUMMARY_KEYS:
                if key in current.outputs and key not in consolidated:
                    consolidated[key] = current.outputs[key]
            assumptions.extend(str(a) for a in current.assumptions)
            warnings.extend(str(w) for w in current.warnings)
        elif stored is not None:
            by_stage[sid] = {
                "status": stored.status.value,
                "model_id": stored.model_id,
                "result_id": stored.result_id,
            }
            if stored.status is ResultStatus.NOT_IMPLEMENTED:
                not_implemented.append(sid)
            else:
                stale_or_failed.append(f"{sid}:{stored.status.value}")
        else:
            by_stage[sid] = {
                "status": node.status.value,
                "implementation_status": node.implementation_status.value,
            }
            if node.implementation_status.value == "NOT_IMPLEMENTED":
                not_implemented.append(sid)

    if current_count == 0:
        warnings.append("No CURRENT stage results available to summarize.")

    result = make_result(
        calculation_type="workflow.performance_summary",
        stage_id=stage_id,
        status=ResultStatus.CURRENT if current_count > 0 else ResultStatus.NOT_CALCULATED,
        model_id="systems.performance_summary",
        model_version="0.1",
        inputs={"stages_considered": list(by_stage.keys())},
        outputs={
            "consolidated": consolidated,
            "by_stage": by_stage,
            "current_stage_count": current_count,
            "not_implemented_stages": not_implemented,
            "stale_or_failed_stages": stale_or_failed,
        },
        assumptions=tuple(dict.fromkeys(assumptions)),
        warnings=tuple(dict.fromkeys(warnings)),
        validity=ValidityInfo(status=ValidityState.UNKNOWN),
        verification=VerificationInfo(
            status="PASS" if current_count > 0 else "UNKNOWN",
            reference="Aggregation of stored CURRENT CalculationResult envelopes only.",
        ),
        source="systems.stages.performance_summary",
        design_revision=design.revision,
    )
    design.store_stage_result(stage_id, result)
    return result
