"""Workflow graph: stage registry and dependency edges."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from systems.contracts.results import ResultStatus

__all__ = (
    "BYPASSABLE_WHEN_UNIMPLEMENTED",
    "PROPULSION_STAGE_SEQUENCE",
    "STAGE_ENGINEERING_NOTES",
    "DependencyRequirement",
    "StageDependency",
    "StageImplementationStatus",
    "WorkflowGraph",
    "WorkflowNode",
    "build_default_propulsion_graph",
    "ordered_stage_ids",
    "stage_index",
)

# Downstream stage may run when the named upstream capability is NOT_IMPLEMENTED.
# The orchestrator must still record the stub result; it must not invent physics.
BYPASSABLE_WHEN_UNIMPLEMENTED: dict[tuple[str, str], str] = {
    ("chamber", "injector"): (
        "Injector orifice/element physics is NOT_IMPLEMENTED; chamber L* sizing "
        "proceeds from performance geometry only."
    ),
    ("nozzle", "cooling"): (
        "Regenerative/film cooling is NOT_IMPLEMENTED; nozzle uses isentropic "
        "1D stations without a cooled-wall model."
    ),
    ("operating_point", "cycle"): (
        "Cycle power balance is NOT_IMPLEMENTED; preliminary operating-point "
        "construction defers the cycle analysis and is not a complete engine design."
    ),
}

# User-facing Rocket Engine order (stages 00–16). Graph edges still govern execution.
PROPULSION_STAGE_SEQUENCE: tuple[str, ...] = (
    "design_project",
    "requirements",
    "propellants",
    "cycle",
    "operating_point",
    "thermochemistry",
    "performance",
    "injector",
    "chamber",
    "thermal",
    "cooling",
    "nozzle",
    "structure",
    "materials",
    "performance_summary",
    "consistency",
    "design_review",
)

STAGE_ENGINEERING_NOTES: dict[str, str] = {
    "design_project": "One PropulsionDesign identity. New/Clone create; Run updates the same design.",
    "requirements": "Authoritative targets (Pc, thrust, O/F, expansion). Changing them marks dependents STALE.",
    "propellants": "Physics registry identity only. Concatenated labels such as LOX/RP-1 are display, not IDs.",
    "cycle": "NOT_IMPLEMENTED — no validated cycle power-balance model exists in COSMOS 0.1 Physics.",
    "operating_point": "Built from requirements and propellants. Gamma/Tc may be explicit analysis assumptions.",
    "thermochemistry": "PARTIAL — NASA CEA is UNAVAILABLE; Tc/γ/MW are ASSUMED when supplied.",
    "performance": "PARTIAL — choked isentropic mass flow and ideal thrust. No loss model.",
    "injector": "NOT_IMPLEMENTED — orifice/element injector design is not in frozen Physics.",
    "chamber": "PARTIAL — preliminary L* geometry from throat area. Injector volume is neglected.",
    "thermal": "PARTIAL — Bartz gas-side HTC at the throat. Gas properties are analysis inputs.",
    "cooling": "NOT_IMPLEMENTED — regenerative/film cooling is not available.",
    "nozzle": "PARTIAL — 1D isentropic stations reused from Performance. MOC/Rao contour is NOT_IMPLEMENTED.",
    "structure": "PARTIAL — thin-wall hoop/longitudinal stress vs handbook yield. Not a certified allowable.",
    "materials": "PARTIAL — Physics handbook catalog lookup. Not MMPDS/ASME certified allowables.",
    "performance_summary": "Aggregation of CURRENT stage results. Does not invent missing physics.",
    "consistency": "Checks required CURRENT results and documented NOT_IMPLEMENTED bypasses.",
    "design_review": "READY only when required implemented stages are CURRENT. Injector/cooling/cycle keep INCOMPLETE.",
}


def ordered_stage_ids(stage_ids: Iterable[str] | None = None) -> tuple[str, ...]:
    """Return stage IDs in 00–16 presentation order, then any extra graph nodes."""

    present = (
        set(PROPULSION_STAGE_SEQUENCE)
        if stage_ids is None
        else {str(item) for item in stage_ids}
    )
    ordered = [
        stage_id for stage_id in PROPULSION_STAGE_SEQUENCE if stage_id in present
    ]
    extra: list[str] = []
    if stage_ids is not None:
        extra = [
            str(item)
            for item in stage_ids
            if str(item) not in PROPULSION_STAGE_SEQUENCE
        ]
    return tuple(ordered + extra)


def stage_index(stage_id: str) -> str:
    try:
        return f"{PROPULSION_STAGE_SEQUENCE.index(stage_id):02d}"
    except ValueError:
        return "--"


class StageImplementationStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    UNAVAILABLE = "UNAVAILABLE"
    OUT_OF_RANGE = "OUT_OF_RANGE"  # stage present but inputs outside model envelope


class DependencyRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    INFORMATIONAL = "INFORMATIONAL"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True, slots=True)
class StageDependency:
    stage_id: str
    requirement: DependencyRequirement = DependencyRequirement.REQUIRED
    reason: str = "Consumed by the downstream calculation."

    def to_canonical_dict(self) -> dict[str, str]:
        return {
            "stage_id": self.stage_id,
            "requirement": self.requirement.value,
            "reason": self.reason,
        }


def _dependency(downstream: str, upstream: str) -> StageDependency:
    reason = BYPASSABLE_WHEN_UNIMPLEMENTED.get((downstream, upstream))
    if reason is not None:
        return StageDependency(upstream, DependencyRequirement.DEFERRED, reason)
    if downstream == "requirements" and upstream == "design_project":
        return StageDependency(
            upstream,
            DependencyRequirement.INFORMATIONAL,
            "Design identity already exists.",
        )
    if downstream == "nozzle" and upstream == "chamber":
        return StageDependency(
            upstream,
            DependencyRequirement.INFORMATIONAL,
            "Ideal 1D stations use performance geometry, not chamber sizing.",
        )
    if downstream == "materials" and upstream == "chamber":
        return StageDependency(
            upstream,
            DependencyRequirement.INFORMATIONAL,
            "Material identity lookup is independent of chamber geometry.",
        )
    if downstream == "performance_summary" and upstream != "performance":
        return StageDependency(
            upstream,
            DependencyRequirement.OPTIONAL,
            "Aggregate only available CURRENT subsystem outputs.",
        )
    return StageDependency(upstream)


@dataclass(slots=True)
class WorkflowNode:
    stage_id: str
    name: str
    dependencies: tuple[StageDependency, ...] = ()
    implementation_status: StageImplementationStatus = (
        StageImplementationStatus.NOT_IMPLEMENTED
    )
    status: ResultStatus = ResultStatus.NOT_CALCULATED
    result_id: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "dependencies": [item.stage_id for item in self.dependencies],
            "dependency_edges": [
                item.to_canonical_dict() for item in self.dependencies
            ],
            "implementation_status": self.implementation_status.value,
            "name": self.name,
            "result_id": self.result_id,
            "stage_id": self.stage_id,
            "status": self.status.value,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, Any]) -> WorkflowNode:
        return cls(
            stage_id=str(data["stage_id"]),
            name=str(data["name"]),
            dependencies=tuple(
                StageDependency(
                    str(item["stage_id"]),
                    DependencyRequirement(str(item["requirement"])),
                    str(item.get("reason", "")),
                )
                for item in data["dependency_edges"]
            )
            if "dependency_edges" in data
            else tuple(
                _dependency(str(data["stage_id"]), str(item))
                for item in (data.get("dependencies") or ())
            ),
            implementation_status=StageImplementationStatus(
                str(
                    data.get(
                        "implementation_status",
                        StageImplementationStatus.NOT_IMPLEMENTED.value,
                    )
                )
            ),
            status=ResultStatus(
                str(data.get("status", ResultStatus.NOT_CALCULATED.value))
            ),
            result_id=None if data.get("result_id") is None else str(data["result_id"]),
        )


@dataclass(slots=True)
class WorkflowGraph:
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)

    def get(self, stage_id: str) -> WorkflowNode:
        return self.nodes[stage_id]

    def dependents(self, stage_id: str, *, data_only: bool = False) -> tuple[str, ...]:
        """Return stages that list ``stage_id`` as a direct dependency."""

        return tuple(
            node.stage_id
            for node in self.nodes.values()
            if any(
                dep.stage_id == stage_id
                and (
                    not data_only
                    or dep.requirement
                    in {
                        DependencyRequirement.REQUIRED,
                        DependencyRequirement.OPTIONAL,
                    }
                )
                for dep in node.dependencies
            )
        )

    def transitive_dependents(
        self, stage_id: str, *, data_only: bool = False
    ) -> tuple[str, ...]:
        """Return all downstream dependents (BFS), excluding ``stage_id``."""

        seen: list[str] = []
        queue = list(self.dependents(stage_id, data_only=data_only))
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.append(current)
            queue.extend(self.dependents(current, data_only=data_only))
        return tuple(seen)

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "nodes": {
                stage_id: node.to_canonical_dict()
                for stage_id, node in sorted(self.nodes.items())
            }
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, Any]) -> WorkflowGraph:
        raw_nodes = dict(data.get("nodes") or {})
        nodes = {
            str(key): WorkflowNode.from_canonical_dict(dict(value))
            for key, value in raw_nodes.items()
        }
        return cls(nodes=nodes)


def build_default_propulsion_graph() -> WorkflowGraph:
    """
    Initial propulsion workflow graph (Phase 1 architecture).

    Cycle is registered but does not block operating_point construction.
    """

    specs: tuple[tuple[str, str, tuple[str, ...], StageImplementationStatus], ...] = (
        ("design_project", "Design Project", (), StageImplementationStatus.PARTIAL),
        (
            "requirements",
            "Requirements",
            ("design_project",),
            StageImplementationStatus.IMPLEMENTED,
        ),
        (
            "propellants",
            "Propellant Definition",
            ("requirements",),
            StageImplementationStatus.IMPLEMENTED,
        ),
        (
            "cycle",
            "Engine Cycle",
            ("requirements",),
            StageImplementationStatus.NOT_IMPLEMENTED,
        ),
        (
            "operating_point",
            "Operating Point",
            ("propellants", "cycle"),
            StageImplementationStatus.IMPLEMENTED,
        ),
        (
            "thermochemistry",
            "Thermochemistry",
            ("operating_point", "propellants"),
            StageImplementationStatus.PARTIAL,
        ),
        (
            "performance",
            "Mass Flow / Performance",
            ("thermochemistry", "operating_point"),
            StageImplementationStatus.PARTIAL,
        ),
        (
            "injector",
            "Injector",
            ("performance",),
            StageImplementationStatus.NOT_IMPLEMENTED,
        ),
        (
            "chamber",
            "Combustion Chamber",
            ("performance", "injector"),
            StageImplementationStatus.PARTIAL,  # L* geometry via Systems Phase 4
        ),
        (
            "thermal",
            "Thermal Analysis",
            ("chamber",),
            StageImplementationStatus.PARTIAL,  # Bartz via Systems Phase 4
        ),
        (
            "cooling",
            "Cooling System",
            ("thermal",),
            StageImplementationStatus.NOT_IMPLEMENTED,  # regen/film not available
        ),
        (
            "materials",
            "Material Selection",
            ("chamber",),
            StageImplementationStatus.PARTIAL,
        ),
        (
            "structure",
            "Structural Analysis",
            ("chamber", "materials"),
            StageImplementationStatus.PARTIAL,  # thin-wall via Systems Phase 4
        ),
        (
            "nozzle",
            "Nozzle",
            ("chamber", "cooling", "performance"),
            StageImplementationStatus.PARTIAL,  # isentropic / area-ratio; no MOC
        ),
        (
            "performance_summary",
            "Engine Performance Summary",
            ("nozzle", "structure", "thermal", "performance"),
            StageImplementationStatus.IMPLEMENTED,  # Phase 6 aggregator
        ),
        (
            "consistency",
            "System Consistency Check",
            ("performance_summary",),
            StageImplementationStatus.IMPLEMENTED,  # Phase 6
        ),
        (
            "design_review",
            "Design Review",
            ("consistency",),
            StageImplementationStatus.IMPLEMENTED,  # Phase 6
        ),
    )
    nodes = {
        stage_id: WorkflowNode(
            stage_id=stage_id,
            name=name,
            dependencies=tuple(_dependency(stage_id, dep) for dep in deps),
            implementation_status=impl,
        )
        for stage_id, name, deps, impl in specs
    }
    return WorkflowGraph(nodes=nodes)
