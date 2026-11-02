"""Workflow state container attached to a propulsion design."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from systems.contracts.results import (
    CalculationResult,
    ResultStatus,
    is_current_displayable,
)
from systems.workflow.graph import (
    DependencyRequirement,
    StageImplementationStatus,
    WorkflowGraph,
    build_default_propulsion_graph,
)
from systems.workflow.invalidation import (
    invalidate_for_input_change,
    invalidate_from_stage,
)

__all__ = ("WorkflowState",)


@dataclass(slots=True)
class WorkflowState:
    graph: WorkflowGraph = field(default_factory=build_default_propulsion_graph)
    # stage_id → current/stale result (historical revisions kept separately)
    results: dict[str, CalculationResult] = field(default_factory=dict)
    result_history: list[CalculationResult] = field(default_factory=list)

    def current_result(self, stage_id: str) -> CalculationResult | None:
        """Return a result only when it is CURRENT (never STALE as current)."""

        result = self.results.get(stage_id)
        if result is None:
            return None
        if not is_current_displayable(result.status):
            return None
        return result

    def store_result(self, stage_id: str, result: CalculationResult) -> None:
        previous = self.results.get(stage_id)
        if previous is not None:
            previous.mark_stale()
            self.result_history.append(previous)
        result.stage_id = stage_id
        self.results[stage_id] = result
        node = self.graph.nodes[stage_id]
        node.status = result.status
        node.result_id = result.result_id

    def mark_not_implemented(self, stage_id: str, reason: str) -> CalculationResult:
        result = CalculationResult(
            calculation_type=f"workflow.{stage_id}",
            status=ResultStatus.NOT_IMPLEMENTED,
            stage_id=stage_id,
            warnings=(reason,),
            errors=({"code": "NOT_IMPLEMENTED", "message": reason, "stage": stage_id},),
        )
        self.store_result(stage_id, result)
        return result

    def invalidate_from(
        self, stage_id: str, *, include_root: bool = False
    ) -> tuple[str, ...]:
        return invalidate_from_stage(
            self.graph, self.results, stage_id, include_root=include_root
        )

    def invalidate_field(self, field: str) -> tuple[str, ...]:
        return invalidate_for_input_change(self.graph, self.results, field)

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "graph": self.graph.to_canonical_dict(),
            "result_history": [
                item.to_canonical_dict() for item in self.result_history
            ],
            "results": {
                key: value.to_canonical_dict()
                for key, value in sorted(self.results.items())
            },
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, Any]) -> WorkflowState:
        graph = WorkflowGraph.from_canonical_dict(dict(data.get("graph") or {}))
        if not graph.nodes:
            graph = build_default_propulsion_graph()
        # Upgrade old placeholder edges, retaining saved results and statuses.
        # The old cooling -> nozzle edge is replaced by contour -> cooling.
        defaults = build_default_propulsion_graph()
        # Only migrate the recognized frozen default, not user/custom edges.
        nozzle = graph.nodes.get("nozzle")
        cooling = graph.nodes.get("cooling")
        if (
            nozzle is not None
            and cooling is not None
            and len(nozzle.dependencies) == 3
            and {(edge.stage_id, edge.requirement) for edge in nozzle.dependencies}
            == {
                ("chamber", DependencyRequirement.INFORMATIONAL),
                ("cooling", DependencyRequirement.DEFERRED),
                ("performance", DependencyRequirement.REQUIRED),
            }
            and len(cooling.dependencies) == 1
            and {(edge.stage_id, edge.requirement) for edge in cooling.dependencies}
            == {("thermal", DependencyRequirement.REQUIRED)}
            and cooling.implementation_status
            is StageImplementationStatus.NOT_IMPLEMENTED
        ):
            nozzle.dependencies = defaults.nodes["nozzle"].dependencies
            cooling.dependencies = defaults.nodes["cooling"].dependencies
            cooling.implementation_status = StageImplementationStatus.PARTIAL
        chamber = graph.nodes.get("chamber")
        if (
            chamber is not None
            and len(chamber.dependencies) == 2
            and {(edge.stage_id, edge.requirement) for edge in chamber.dependencies}
            == {
                ("performance", DependencyRequirement.REQUIRED),
                ("injector", DependencyRequirement.DEFERRED),
            }
        ):
            chamber.dependencies = defaults.nodes["chamber"].dependencies
        injector = graph.nodes.get("injector")
        if (
            injector is not None
            and injector.implementation_status
            is StageImplementationStatus.NOT_IMPLEMENTED
        ):
            injector.implementation_status = StageImplementationStatus.PARTIAL
        results_raw = dict(data.get("results") or {})
        results = {
            str(key): CalculationResult.from_canonical_dict(dict(value))
            for key, value in results_raw.items()
        }
        history = [
            CalculationResult.from_canonical_dict(dict(item))
            for item in (data.get("result_history") or [])
        ]
        return cls(graph=graph, results=results, result_history=history)
