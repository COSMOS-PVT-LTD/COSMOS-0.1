"""Dependency invalidation for propulsion workflow results."""

from __future__ import annotations

from systems.contracts.results import CalculationResult, ResultStatus
from systems.workflow.graph import WorkflowGraph

__all__ = (
    "INPUT_FIELD_ROOTS",
    "invalidate_from_stage",
    "invalidate_for_input_change",
)


# Map engineering input categories → root stage whose dependents go STALE.
INPUT_FIELD_ROOTS: dict[str, str] = {
    "target_chamber_pressure": "requirements",
    "chamber_pressure": "operating_point",
    "mixture_ratio": "propellants",
    "propellant": "propellants",
    "oxidizer_id": "propellants",
    "fuel_id": "propellants",
    "ambient_pressure": "requirements",
    "ambient_temperature": "requirements",
    "geometry": "chamber",
    "material": "materials",
    "expansion_ratio": "requirements",
    "mach": "nozzle",
    "gamma": "operating_point",
}


def invalidate_from_stage(
    graph: WorkflowGraph,
    results: dict[str, CalculationResult],
    stage_id: str,
    *,
    include_root: bool = False,
) -> tuple[str, ...]:
    """
    Mark dependent stage results STALE. Preserve historical CURRENT→STALE.

    Returns the list of stage IDs that were marked stale.
    """

    targets = list(graph.transitive_dependents(stage_id))
    if include_root:
        targets = [stage_id, *targets]
    marked: list[str] = []
    for dependent_id in targets:
        node = graph.nodes.get(dependent_id)
        if node is None:
            continue
        if node.status is ResultStatus.CURRENT:
            node.status = ResultStatus.STALE
        result = results.get(dependent_id)
        if result is not None and result.status is ResultStatus.CURRENT:
            result.mark_stale()
            marked.append(dependent_id)
        elif node.status is ResultStatus.STALE:
            marked.append(dependent_id)
    return tuple(dict.fromkeys(marked))


def invalidate_for_input_change(
    graph: WorkflowGraph,
    results: dict[str, CalculationResult],
    field: str,
) -> tuple[str, ...]:
    """Invalidate from the stage that owns ``field``."""

    root = INPUT_FIELD_ROOTS.get(field)
    if root is None:
        # Unknown fields invalidate from requirements as a conservative default
        # only when they look like requirement keys; otherwise no-op.
        return ()
    return invalidate_from_stage(graph, results, root, include_root=True)
