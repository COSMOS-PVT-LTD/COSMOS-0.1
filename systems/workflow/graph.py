"""Workflow graph: stage registry and dependency edges."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from systems.contracts.results import ResultStatus

__all__ = (
    "StageImplementationStatus",
    "WorkflowGraph",
    "WorkflowNode",
    "build_default_propulsion_graph",
)


class StageImplementationStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    UNAVAILABLE = "UNAVAILABLE"
    OUT_OF_RANGE = "OUT_OF_RANGE"  # stage present but inputs outside model envelope


@dataclass(slots=True)
class WorkflowNode:
    stage_id: str
    name: str
    dependencies: tuple[str, ...] = ()
    implementation_status: StageImplementationStatus = (
        StageImplementationStatus.NOT_IMPLEMENTED
    )
    status: ResultStatus = ResultStatus.NOT_CALCULATED
    result_id: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "dependencies": list(self.dependencies),
            "implementation_status": self.implementation_status.value,
            "name": self.name,
            "result_id": self.result_id,
            "stage_id": self.stage_id,
            "status": self.status.value,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> WorkflowNode:
        return cls(
            stage_id=str(data["stage_id"]),
            name=str(data["name"]),
            dependencies=tuple(str(item) for item in (data.get("dependencies") or ())),
            implementation_status=StageImplementationStatus(
                str(
                    data.get(
                        "implementation_status",
                        StageImplementationStatus.NOT_IMPLEMENTED.value,
                    )
                )
            ),
            status=ResultStatus(str(data.get("status", ResultStatus.NOT_CALCULATED.value))),
            result_id=None if data.get("result_id") is None else str(data["result_id"]),
        )


@dataclass(slots=True)
class WorkflowGraph:
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)

    def get(self, stage_id: str) -> WorkflowNode:
        return self.nodes[stage_id]

    def dependents(self, stage_id: str) -> tuple[str, ...]:
        """Return stages that list ``stage_id`` as a direct dependency."""

        return tuple(
            node.stage_id
            for node in self.nodes.values()
            if stage_id in node.dependencies
        )

    def transitive_dependents(self, stage_id: str) -> tuple[str, ...]:
        """Return all downstream dependents (BFS), excluding ``stage_id``."""

        seen: list[str] = []
        queue = list(self.dependents(stage_id))
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.append(current)
            queue.extend(self.dependents(current))
        return tuple(seen)

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "nodes": {
                stage_id: node.to_canonical_dict()
                for stage_id, node in sorted(self.nodes.items())
            }
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> WorkflowGraph:
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
        ("requirements", "Requirements", ("design_project",), StageImplementationStatus.IMPLEMENTED),
        ("propellants", "Propellant Definition", ("requirements",), StageImplementationStatus.IMPLEMENTED),
        ("cycle", "Engine Cycle", ("requirements",), StageImplementationStatus.NOT_IMPLEMENTED),
        (
            "operating_point",
            "Operating Point",
            ("propellants",),
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
            dependencies=deps,
            implementation_status=impl,
        )
        for stage_id, name, deps, impl in specs
    }
    return WorkflowGraph(nodes=nodes)
