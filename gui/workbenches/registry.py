"""Registered COSMOS engineering workbenches."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("WORKBENCH_PAGES", "WorkbenchDefinition", "workbench_by_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkbenchDefinition:
    workbench_id: str
    title: str
    page: int
    route: str
    status: str
    description: str
    modules: tuple[str, ...] = ()


WORKBENCH_PAGES: tuple[tuple[WorkbenchDefinition, ...], ...] = (
    (
        WorkbenchDefinition(
            workbench_id="rocket-engine",
            title="Rocket Engine",
            page=1,
            route="/app/workbench/rocket-engine",
            status="active",
            description="Engine design modules for chamber, injector, cooling, and nozzle.",
            modules=(
                "Engine Design",
                "Nozzle Optimization",
                "Injectors",
                "Ignitor",
                "Regen Channel",
                "Automatic CAD Generation From Data",
            ),
        ),
        WorkbenchDefinition(
            workbench_id="turbopumps",
            title="Turbopumps",
            page=1,
            route="/app/workbench/turbopumps",
            status="planned",
            description="Pump, turbine, and feed-system rotordynamics.",
        ),
        WorkbenchDefinition(
            workbench_id="pid",
            title="Piping Instrumentation & Documentation",
            page=1,
            route="/app/workbench/pid",
            status="planned",
            description="P&ID authoring, instrumentation, and documentation control.",
        ),
        WorkbenchDefinition(
            workbench_id="structures",
            title="Structures",
            page=1,
            route="/app/workbench/structures",
            status="planned",
            description="Structural analysis, loads, and hardware substantiation.",
        ),
    ),
    (
        WorkbenchDefinition(
            workbench_id="rocket-staging",
            title="Rocket Staging",
            page=2,
            route="/app/workbench/rocket-staging",
            status="planned",
            description="Stage sizing, mass properties, and mission envelope planning.",
        ),
        WorkbenchDefinition(
            workbench_id="manufacturing",
            title="Manufacturing",
            page=2,
            route="/app/workbench/manufacturing",
            status="planned",
            description="Process planning, tooling, and build readiness.",
        ),
        WorkbenchDefinition(
            workbench_id="simulation",
            title="Simulation",
            page=2,
            route="/app/workbench/simulation",
            status="planned",
            description="CFD, FEA, and coupled physics simulation launchers.",
        ),
        WorkbenchDefinition(
            workbench_id="visualization",
            title="Visualization and Graphs",
            page=2,
            route="/app/workbench/visualization",
            status="planned",
            description="Engineering plots, dashboards, and result visualization.",
        ),
    ),
    (
        WorkbenchDefinition(
            workbench_id="documentation",
            title="Documentation",
            page=3,
            route="/app/workbench/documentation",
            status="planned",
            description="Controlled engineering documentation and release packages.",
        ),
        WorkbenchDefinition(
            workbench_id="code-comparison",
            title="Code Comparison with OTCS",
            page=3,
            route="/app/workbench/code-comparison",
            status="planned",
            description="Traceability against OTCS and external reference implementations.",
        ),
        WorkbenchDefinition(
            workbench_id="plm",
            title="PLM",
            page=3,
            route="/app/workbench/plm",
            status="planned",
            description="Product lifecycle, revisions, and configuration management.",
        ),
        WorkbenchDefinition(
            workbench_id="knowledge",
            title="Maharshi Bharadwaj",
            page=3,
            route="/app/workbench/knowledge",
            status="active",
            description="COSMOS knowledge infrastructure — governed intake, review, search, and engineering chat.",
        ),
    ),
)


def workbench_by_id(workbench_id: str) -> WorkbenchDefinition | None:
    for page in WORKBENCH_PAGES:
        for item in page:
            if item.workbench_id == workbench_id:
                return item
    return None
