"""Workflow state container attached to a propulsion design."""

from __future__ import annotations

from dataclasses import dataclass, field

from systems.contracts.results import CalculationResult, ResultStatus, is_current_displayable
from systems.workflow.graph import WorkflowGraph, build_default_propulsion_graph
from systems.workflow.invalidation import invalidate_for_input_change, invalidate_from_stage

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

    def invalidate_from(self, stage_id: str, *, include_root: bool = False) -> tuple[str, ...]:
        return invalidate_from_stage(
            self.graph, self.results, stage_id, include_root=include_root
        )

    def invalidate_field(self, field: str) -> tuple[str, ...]:
        return invalidate_for_input_change(self.graph, self.results, field)

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "graph": self.graph.to_canonical_dict(),
            "result_history": [item.to_canonical_dict() for item in self.result_history],
            "results": {
                key: value.to_canonical_dict()
                for key, value in sorted(self.results.items())
            },
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> WorkflowState:
        graph = WorkflowGraph.from_canonical_dict(dict(data.get("graph") or {}))
        if not graph.nodes:
            graph = build_default_propulsion_graph()
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
