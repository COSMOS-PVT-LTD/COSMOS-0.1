"""Unit tests for workflow graph and invalidation."""

from __future__ import annotations

from systems.contracts.results import CalculationResult, ResultStatus
from systems.projects.models import PropulsionDesign
from systems.workflow.graph import build_default_propulsion_graph
from systems.workflow.invalidation import invalidate_from_stage


def test_stage_registry_has_seventeen_nodes() -> None:
    graph = build_default_propulsion_graph()
    assert len(graph.nodes) == 17
    assert "design_project" in graph.nodes
    assert "design_review" in graph.nodes
    assert graph.get("cycle").implementation_status.value == "NOT_IMPLEMENTED"


def test_dependencies_follow_architecture() -> None:
    graph = build_default_propulsion_graph()
    assert "propellants" in graph.get("operating_point").dependencies
    assert "operating_point" in graph.get("thermochemistry").dependencies
    assert "chamber" in graph.get("nozzle").dependencies


def test_invalidation_marks_dependents_stale_not_deleted() -> None:
    design = PropulsionDesign(name="Invalidate")
    nozzle = CalculationResult(
        calculation_type="compressible.isentropic",
        status=ResultStatus.CURRENT,
        stage_id="nozzle",
    )
    summary = CalculationResult(
        calculation_type="performance.summary",
        status=ResultStatus.CURRENT,
        stage_id="performance_summary",
    )
    design.workflow.store_result("nozzle", nozzle)
    design.workflow.store_result("performance_summary", summary)

    marked = invalidate_from_stage(
        design.workflow.graph,
        design.workflow.results,
        "nozzle",
        include_root=False,
    )
    assert "performance_summary" in marked
    assert design.workflow.results["performance_summary"].status is ResultStatus.STALE
    assert design.workflow.current_result("performance_summary") is None
    # Prior result retained in place as STALE (not deleted).
    assert design.workflow.results["performance_summary"].calculation_type == "performance.summary"


def test_input_change_invalidates_through_design() -> None:
    design = PropulsionDesign(name="Pc change")
    design.workflow.store_result(
        "operating_point",
        CalculationResult(
            calculation_type="operating_point",
            status=ResultStatus.CURRENT,
            stage_id="operating_point",
        ),
    )
    design.workflow.store_result(
        "nozzle",
        CalculationResult(
            calculation_type="compressible.isentropic",
            status=ResultStatus.CURRENT,
            stage_id="nozzle",
        ),
    )
    marked = design.record_input_change("chamber_pressure", 1.0e6, 2.0e6)
    assert design.revision == 1
    assert design.workflow.results["operating_point"].status is ResultStatus.STALE
    assert "nozzle" in marked or design.workflow.results["nozzle"].status is ResultStatus.STALE
