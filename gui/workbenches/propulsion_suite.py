"""Rocket Engine propulsion design suite module catalog (RPA/RPL-inspired)."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("PROPULSION_SUITE_MODULES", "suite_module_by_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class SuiteModule:
    module_id: str
    title: str
    group: str
    description: str
    status: str  # live | partial | planned
    physics_ops: tuple[str, ...] = ()
    reference_note: str = ""


PROPULSION_SUITE_MODULES: tuple[SuiteModule, ...] = (
    SuiteModule(
        module_id="workflow-analysis",
        title="Workflow Analysis (E2E)",
        group="Workflow",
        description="End-to-end Systems workflow through summary, consistency, design review, and export.",
        status="live",
        physics_ops=("choked_flow", "area_mach", "thrust", "bartz", "thin_wall"),
        reference_note="Phase 3–6 orchestrated analysis via systems package.",
    ),
    SuiteModule(
        module_id="engine-definition",
        title="Engine Definition",
        group="Performance",
        description="High-level engine targets: thrust, chamber pressure, mixture ratio, nozzle expansion.",
        status="partial",
        reference_note="Inspired by RPA Engine definition / RPL workbench solve inputs.",
    ),
    SuiteModule(
        module_id="propellants-combustion",
        title="Propellants & Combustion",
        group="Thermochemistry",
        description="Propellant selection and combustion thermochemistry (CEA interface — not executed in GUI yet).",
        status="planned",
        reference_note="RPA Propellant and combustion properties; NASA CEA boundary preserved.",
    ),
    SuiteModule(
        module_id="chamber-sizing",
        title="Thrust Chamber Sizing",
        group="Geometry",
        description="Chamber / throat / exit area relationships from mass flow and compressible flow.",
        status="partial",
        physics_ops=("choked_flow", "area_mach"),
        reference_note="RPA Thrust chamber size specification.",
    ),
    SuiteModule(
        module_id="nozzle-flow",
        title="Nozzle Flow",
        group="Gasdynamics",
        description="Isentropic stagnation relations and Area–Mach forward/inverse (Anderson).",
        status="live",
        physics_ops=("isentropic_stagnation", "area_mach"),
        reference_note="RPA Nozzle flow model; RPL quasi-1D nozzle verification concepts.",
    ),
    SuiteModule(
        module_id="nozzle-contour",
        title="Nozzle Contour",
        group="Geometry",
        description="Contour generation (MOC assigned to Numerics — not available in 0.1 GUI).",
        status="planned",
        reference_note="RPA nozzle wall contour optimization; COSMOS MOC deferred to numerics.",
    ),
    SuiteModule(
        module_id="heat-transfer",
        title="Heat Transfer & Cooling",
        group="Thermal",
        description="Gas-side Bartz heat-transfer coefficient with optional curvature.",
        status="live",
        physics_ops=("bartz",),
        reference_note="RPA Thermal analysis; Bartz SI Nusselt form in Physics.",
    ),
    SuiteModule(
        module_id="injectors",
        title="Injectors",
        group="Feed",
        description="Injector design criteria and orifice sizing (engineering methods — future).",
        status="planned",
        reference_note="NASA liquid rocket injector design criteria (knowledge/engineering).",
    ),
    SuiteModule(
        module_id="structures",
        title="Chamber Structures",
        group="Structures",
        description="Thin-wall hoop/longitudinal stress vs material yield (Physics constitutive).",
        status="partial",
        physics_ops=("thin_wall", "material_yield"),
        reference_note="RPL structural checks; COSMOS PHYS-006/007 foundation.",
    ),
    SuiteModule(
        module_id="cycle-feed",
        title="Cycle / Feed System",
        group="System",
        description="Pressure-fed / pump-fed cycle analysis (deferred — not in frozen Physics batch).",
        status="planned",
        reference_note="RPA cycle module (returning in future RPA); RPL Engine Workbench.",
    ),
)


def suite_module_by_id(module_id: str) -> SuiteModule | None:
    for item in PROPULSION_SUITE_MODULES:
        if item.module_id == module_id:
            return item
    return None
