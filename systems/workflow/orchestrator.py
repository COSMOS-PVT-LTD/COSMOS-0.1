"""Phase 3/4/6 orchestration for propulsion workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from systems.contracts.results import CalculationResult, ResultStatus
from systems.projects.models import PropulsionDesign
from systems.stages.chamber import run_chamber_stage
from systems.stages.consistency import run_consistency_stage
from systems.stages.design_review import run_design_review_stage
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

__all__ = (
    "Phase3Result",
    "run_phase3_chain",
    "run_phase4_chain",
    "run_phase6_chain",
    "update_phase3_graph_status",
    "update_phase4_graph_status",
    "update_phase6_graph_status",
)


@dataclass(slots=True)
class Phase3Result:
    design: PropulsionDesign
    stages: dict[str, CalculationResult]
    ok: bool


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
    ok = all(stages[key].status is ResultStatus.CURRENT for key in critical)
    return Phase3Result(design=design, stages=stages, ok=ok)


def run_phase4_chain(
    design: PropulsionDesign,
    *,
    characteristic_length_m: float | None = None,
    contraction_ratio: float | None = None,
    wall_thickness_m: float | None = None,
    material_id: str = "stainless_304",
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
    stages["thermal"] = run_thermal_stage(design)  # type: ignore[assignment]
    cool = run_cooling_stage(design)
    design.store_stage_result("cooling", cool)
    stages["cooling"] = cool  # type: ignore[assignment]
    stages["materials"] = run_materials_stage(design, material_id=material_id)  # type: ignore[assignment]
    stages["structure"] = run_structure_stage(  # type: ignore[assignment]
        design,
        wall_thickness_m=wall_thickness_m,
    )
    ok = all(
        stages[key].status is ResultStatus.CURRENT
        for key in ("chamber", "thermal", "materials", "structure")
    )
    return Phase3Result(design=design, stages=stages, ok=ok)


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
    ok = all(
        stages[key].status is ResultStatus.CURRENT
        for key in ("performance_summary", "consistency", "design_review")
    )
    return Phase3Result(design=design, stages=stages, ok=ok)
