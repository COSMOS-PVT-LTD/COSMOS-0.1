"""Phase 3/4/6 orchestration for propulsion workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.quantity import Quantity
from systems.contracts.results import CalculationResult, ResultStatus
from systems.projects.models import PropulsionDesign
from systems.stages.chamber import run_chamber_stage
from systems.stages.consistency import run_consistency_stage
from systems.stages.design_review import run_design_review_stage
from systems.stages.nozzle import run_nozzle_stage
from systems.stages.operating_point import run_operating_point_stage
from systems.stages.performance import run_performance_stage
from systems.stages.performance_summary import run_performance_summary_stage
from systems.stages.propellants import run_propellants_stage
from systems.stages.requirements import run_requirements_stage
from systems.stages.structure import (
    run_cooling_stage,
    run_injector_stage,
    run_materials_stage,
    run_structure_stage,
)
from systems.stages.thermal import run_thermal_stage
from systems.stages.thermochemistry import run_thermochemistry_stage
from systems.workflow.graph import StageImplementationStatus
from systems.workflow.readiness import readiness_payload

__all__ = (
    "Phase3Result",
    "run_phase3_chain",
    "run_phase4_chain",
    "run_phase6_chain",
    "update_phase3_graph_status",
    "update_phase4_graph_status",
    "update_phase6_graph_status",
)


def _phase_status(
    stages: dict[str, CalculationResult],
    *,
    required: tuple[str, ...],
) -> tuple[bool, str]:
    """Return (ok, phase_status) without treating NOT_IMPLEMENTED stubs as success."""

    required_ok = all(
        key in stages and stages[key].status is ResultStatus.CURRENT for key in required
    )
    failed = any(result.status in {ResultStatus.FAILED, ResultStatus.OUT_OF_RANGE, ResultStatus.STALE} for result in stages.values())
    unimplemented = any(
        result.status is ResultStatus.NOT_IMPLEMENTED for result in stages.values()
    )
    if failed or not required_ok:
        return False, "FAILED"
    if unimplemented:
        return True, "PARTIAL"
    return True, "COMPLETE"


@dataclass(slots=True)
class Phase3Result:
    design: PropulsionDesign
    stages: dict[str, CalculationResult]
    ok: bool
    phase_status: str = "COMPLETE"

    @property
    def execution_ok(self) -> bool:
        """Compatibility `ok` reports phase execution, never design completeness."""
        return self.ok

    @property
    def readiness(self) -> dict[str, object]:
        return readiness_payload(self.design.workflow)


def update_phase3_graph_status(design: PropulsionDesign) -> None:
    graph = design.workflow.graph
    graph.get("requirements").implementation_status = StageImplementationStatus.IMPLEMENTED
    graph.get("propellants").implementation_status = StageImplementationStatus.IMPLEMENTED
    graph.get("operating_point").implementation_status = StageImplementationStatus.IMPLEMENTED
    graph.get("thermochemistry").implementation_status = StageImplementationStatus.PARTIAL
    graph.get("performance").implementation_status = StageImplementationStatus.PARTIAL


def update_phase4_graph_status(design: PropulsionDesign) -> None:
    graph = design.workflow.graph
    graph.get("injector").implementation_status = StageImplementationStatus.NOT_IMPLEMENTED
    graph.get("chamber").implementation_status = StageImplementationStatus.PARTIAL
    graph.get("thermal").implementation_status = StageImplementationStatus.PARTIAL
    graph.get("cooling").implementation_status = StageImplementationStatus.NOT_IMPLEMENTED
    graph.get("materials").implementation_status = StageImplementationStatus.PARTIAL
    graph.get("structure").implementation_status = StageImplementationStatus.PARTIAL
    graph.get("nozzle").implementation_status = StageImplementationStatus.PARTIAL


def run_phase3_chain(
    design: PropulsionDesign,
    *,
    chamber_temperature_k: float | None = None,
    gamma: float | None = None,
    molecular_weight_kg_per_mol: float | None = None,
    throat_area_m2: float | None = None,
    expansion_ratio: float | None = None,
    thermochemistry_engine: Any = None,
) -> Phase3Result:
    update_phase3_graph_status(design)
    stages: dict[str, CalculationResult] = {}
    stages["requirements"] = run_requirements_stage(design)  # type: ignore[assignment]
    stages["propellants"] = run_propellants_stage(design)  # type: ignore[assignment]
    stages["operating_point"] = run_operating_point_stage(  # type: ignore[assignment]
        design,
        chamber_temperature=chamber_temperature_k,
        gamma=gamma,
        molecular_weight_kg_per_mol=molecular_weight_kg_per_mol,
    )
    stages["thermochemistry"] = run_thermochemistry_stage(  # type: ignore[assignment]
        design,
        engine=thermochemistry_engine,
        assume_chamber_temperature_k=chamber_temperature_k,
        assume_gamma=gamma,
        assume_molar_mass_kg_per_mol=molecular_weight_kg_per_mol,
    )
    stages["performance"] = run_performance_stage(  # type: ignore[assignment]
        design,
        throat_area_m2=throat_area_m2,
        expansion_ratio=expansion_ratio,
    )
    critical = ("requirements", "propellants", "operating_point", "performance")
    ok, phase_status = _phase_status(stages, required=critical)
    if any(
        stages[key].status is ResultStatus.NOT_IMPLEMENTED
        for key in stages
        if key not in critical
    ) and ok:
        phase_status = "PARTIAL"
    thermo = stages.get("thermochemistry")
    if (
        ok
        and thermo is not None
        and thermo.status is ResultStatus.CURRENT
        and any("ASSUMED" in str(item).upper() or "assum" in str(item).lower() for item in thermo.assumptions)
    ):
        phase_status = "PARTIAL"
    return Phase3Result(design=design, stages=stages, ok=ok, phase_status=phase_status)


def run_phase4_chain(
    design: PropulsionDesign,
    *,
    characteristic_length_m: float | None = None,
    contraction_ratio: float | None = None,
    wall_thickness_m: float | None = None,
    material_id: str | None = None,
    external_pressure: Quantity | None = None,
    external_pressure_source: str | None = None,
    material_temperature_k: float | None = None,
    viscosity_pa_s: float | None = None,
    conductivity_w_m_k: float | None = None,
    cp_j_kg_k: float | None = None,
    wall_temperature_k: float | None = None,
    throat_curvature_radius_m: float | None = None,
) -> Phase3Result:
    """Run injector→chamber→thermal→cooling→materials→structure after Phase 3."""

    update_phase4_graph_status(design)
    stages: dict[str, CalculationResult] = {}
    inj = run_injector_stage(design)
    design.store_stage_result("injector", inj)
    stages["injector"] = inj  # type: ignore[assignment]
    stages["chamber"] = run_chamber_stage(  # type: ignore[assignment]
        design,
        characteristic_length_m=characteristic_length_m,
        contraction_ratio=contraction_ratio,
    )
    stages["thermal"] = run_thermal_stage(
        design, viscosity_pa_s=viscosity_pa_s, conductivity_w_m_k=conductivity_w_m_k,
        cp_j_kg_k=cp_j_kg_k, wall_temperature_k=wall_temperature_k,
        throat_curvature_radius_m=throat_curvature_radius_m,
    )
    cool = run_cooling_stage(design)
    design.store_stage_result("cooling", cool)
    stages["cooling"] = cool  # type: ignore[assignment]
    stages["materials"] = run_materials_stage(design, material_id=material_id)  # type: ignore[assignment]
    stages["structure"] = run_structure_stage(  # type: ignore[assignment]
        design,
        wall_thickness_m=wall_thickness_m,
        external_pressure=external_pressure,
        external_pressure_source=external_pressure_source,
        material_temperature_k=material_temperature_k,
    )
    stages["nozzle"] = run_nozzle_stage(design)  # type: ignore[assignment]
    ok, phase_status = _phase_status(
        stages,
        required=("chamber", "thermal", "materials", "structure"),
    )
    return Phase3Result(design=design, stages=stages, ok=ok, phase_status=phase_status)


def update_phase6_graph_status(design: PropulsionDesign) -> None:
    graph = design.workflow.graph
    graph.get("performance_summary").implementation_status = (
        StageImplementationStatus.IMPLEMENTED
    )
    graph.get("consistency").implementation_status = StageImplementationStatus.IMPLEMENTED
    graph.get("design_review").implementation_status = StageImplementationStatus.IMPLEMENTED


def run_phase6_chain(design: PropulsionDesign) -> Phase3Result:
    """
    Run Performance Summary → Consistency → Design Review.

    Expects Phase 3 (and preferably Phase 4) results already on the design.
    """

    update_phase6_graph_status(design)
    stages: dict[str, CalculationResult] = {}
    stages["performance_summary"] = run_performance_summary_stage(design)  # type: ignore[assignment]
    stages["consistency"] = run_consistency_stage(design)  # type: ignore[assignment]
    stages["design_review"] = run_design_review_stage(design)  # type: ignore[assignment]
    ok, phase_status = _phase_status(
        stages,
        required=("performance_summary", "consistency", "design_review"),
    )
    review = stages.get("design_review")
    if review is not None and review.outputs.get("review_verdict") in {"INCOMPLETE", "BLOCKED"}:
        phase_status = "PARTIAL" if review.outputs.get("review_verdict") == "INCOMPLETE" else "FAILED"
        if review.outputs.get("review_verdict") == "BLOCKED":
            ok = False
    return Phase3Result(design=design, stages=stages, ok=ok, phase_status=phase_status)
