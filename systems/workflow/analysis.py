"""Run ready engineering stages and retain actionable input/dependency gaps.

No new physics, guessed material/fluid properties or cycle-stage promotion.
The API captures the complete command before this Systems orchestration runs.
"""
from systems.contracts.results import ResultStatus
from systems.stages._helpers import make_result
from systems.stages.chamber import run_chamber_stage
from systems.stages.nozzle import run_nozzle_stage
from systems.stages.structure import (
    run_cooling_stage,
    run_injector_stage,
    run_materials_stage,
    run_structure_stage,
)
from systems.stages.thermal import run_thermal_stage
from systems.workflow.orchestrator import run_phase6_chain, update_phase4_graph_status
from systems.workflow.readiness import dependency_assessment


def run_configured_analysis(design):
    """Independent stages are not abandoned because a sibling needs input."""
    update_phase4_graph_status(design)
    results, requests = {}, []

    def needs(stage, field):
        cfg = design.subsystem_inputs.get(stage, {})
        retained = getattr(design, {"chamber": "chamber_design", "thermal": "thermal_design",
                                  "materials": "material_selection", "structure": "structural_design"}.get(stage, "chamber_design")) or {}
        aliases = {"material_id": "chamber_material_id", "external_pressure_pa": "external_pressure"}
        return cfg.get(field) is None and retained.get(aliases.get(field, field)) is None

    def await_inputs(stage, fields=(), blockers=()):
        request = {"stage_id": stage, "fields": list(fields), "blocked_by": list(blockers),
                   "action": "Configure this stage's explicit engineering inputs." if fields else "Calculate the named upstream stages first."}
        requests.append(request)
        result = make_result(calculation_type=stage+".awaiting_inputs", stage_id=stage,
            status=ResultStatus.NOT_CALCULATED, design_revision=design.revision,
            inputs={"input_request": request}, outputs={"execution_state": "INPUT_REQUIRED" if fields else "DEPENDENCY_BLOCKED"},
            warnings=(request["action"],))
        design.store_stage_result(stage, result)
        results[stage] = result

    def run(stage, runner, fields=(), **kwargs):
        blockers = [row["stage_id"] for row in dependency_assessment(design.workflow, stage)
                    if row["requirement"] == "REQUIRED" and row["satisfied"] is False]
        if fields or blockers:
            await_inputs(stage, fields, blockers)
        else:
            results[stage] = runner(design, **kwargs)

    for stage, runner in (("injector", run_injector_stage), ("chamber", run_chamber_stage),
                          ("nozzle", run_nozzle_stage), ("thermal", run_thermal_stage),
                          ("cooling", run_cooling_stage), ("materials", run_materials_stage),
                          ("structure", run_structure_stage)):
        cfg = design.subsystem_inputs.get(stage, {})
        if stage in {"injector", "cooling"}:
            from systems.configuration.subsystems import SUBSYSTEM_FIELDS
            # Injector/cooling's own validators retain detailed invalid-input errors.
            fields = ["subsystem_inputs."+stage] if not cfg else []
            if cfg:
                required = SUBSYSTEM_FIELDS[stage] if stage == "injector" else {
                    key for key in SUBSYSTEM_FIELDS[stage] if not key.startswith("film_")}
                if stage == "cooling":
                    required.add("film_mode")
                    if cfg.get("film_mode") == "gaseous_slot":
                        required |= {key for key in SUBSYSTEM_FIELDS[stage] if key.startswith("film_")}
                fields = sorted(key for key in required if cfg.get(key) is None or cfg.get(key) == "")
        elif stage == "nozzle":
            from systems.configuration.subsystems import SUBSYSTEM_FIELDS
            fields = sorted(SUBSYSTEM_FIELDS[stage] - cfg.keys())
        else:
            required = {"chamber": ("characteristic_length_m", "contraction_ratio"),
                        "thermal": ("wall_temperature_k",), "materials": ("material_id",),
                        "structure": ("wall_thickness_m", "external_pressure_pa", "material_temperature_k")}[stage]
            fields = [key for key in required if needs(stage, key)]
            if stage == "thermal" and cfg.get("property_mode", "EXPLICIT") == "EXPLICIT":
                fields += [key for key in ("viscosity_pa_s", "conductivity_w_m_k", "cp_j_kg_k") if needs(stage, key)]
        run(stage, runner, fields, **({"require_contour": True} if stage == "nozzle" else {}))

    # Summary aggregates available results; review is retained even if incomplete.
    summary_blockers = [r["stage_id"] for r in dependency_assessment(design.workflow, "performance_summary")
                        if r["requirement"] == "REQUIRED" and r["satisfied"] is False]
    if not summary_blockers:
        results.update(run_phase6_chain(design).stages)
    else:
        for stage in ("performance_summary", "consistency", "design_review"):
            await_inputs(stage, blockers=summary_blockers)
    return results, requests
