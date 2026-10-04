"""Pressure boundaries, material identity, defaults and dependency contracts."""

import pytest

from core.quantity import Quantity
from physics.quantities import metre, pascal
from systems.contracts.results import CalculationResult, ResultStatus
from systems.projects.models import PropulsionDesign
from systems.stages._helpers import make_result, stage_guard
from systems.stages.chamber import run_chamber_stage
from systems.stages.structure import run_materials_stage, run_structure_stage
from systems.workflow.graph import (
    DependencyRequirement,
    StageDependency,
    WorkflowGraph,
    WorkflowNode,
)
from systems.workflow.state import WorkflowState


def structural_design() -> PropulsionDesign:
    design = PropulsionDesign(name="Pressure-boundary regression")
    design.operating_point.chamber_pressure = pascal(10e6)
    design.chamber_design = {"chamber_diameter_m": 0.2}
    for sid in ("chamber", "materials"):
        design.workflow.store_result(
            sid, CalculationResult(calculation_type=sid, status=ResultStatus.CURRENT)
        )
    design.material_selection = {"chamber_material_id": "stainless_304"}
    return design


@pytest.mark.parametrize("external,delta", [(0, 10e6), (2e6, 8e6), (10e6, 0)])
def test_pressure_differential_invariants(external: float, delta: float) -> None:
    design = structural_design()
    result = run_structure_stage(
        design,
        wall_thickness_m=0.005,
        external_pressure=pascal(external),
        external_pressure_source="test outer boundary",
        material_temperature_k=300,
    )
    assert result.status is ResultStatus.CURRENT
    assert Quantity.from_canonical_dict(
        result.inputs["pressure_differential"]
    ).to_si() == pytest.approx(delta)
    assert result.inputs["external_pressure_source"] == "test outer boundary"
    assert Quantity.from_canonical_dict(
        result.outputs["hoop_stress"]
    ).to_si() == pytest.approx(delta * 0.1 / 0.005)
    assert Quantity.from_canonical_dict(
        result.outputs["longitudinal_stress"]
    ).to_si() == pytest.approx(delta * 0.1 / 0.01)


@pytest.mark.parametrize(
    "pressure,status",
    [
        (metre(2), ResultStatus.FAILED),
        (pascal(-1), ResultStatus.FAILED),
        (pascal(11e6), ResultStatus.OUT_OF_RANGE),
    ],
)
def test_invalid_external_loading_fails(
    pressure: Quantity, status: ResultStatus
) -> None:
    result = run_structure_stage(
        structural_design(),
        wall_thickness_m=0.005,
        external_pressure=pressure,
        material_temperature_k=300,
    )
    assert result.status is status
    assert not result.outputs
    assert result.errors[0]["stage"] == "structure"


def test_thick_wall_is_out_of_range() -> None:
    result = run_structure_stage(
        structural_design(),
        wall_thickness_m=0.02,
        external_pressure=pascal(0),
        material_temperature_k=300,
    )
    assert result.status is ResultStatus.OUT_OF_RANGE
    assert not result.outputs


@pytest.mark.parametrize("material", ["stainless_304", "aluminum_6061_t6"])
def test_requested_known_material_is_used(material: str) -> None:
    design = structural_design()
    assert (
        run_materials_stage(design, material_id=material).status is ResultStatus.CURRENT
    )
    result = run_structure_stage(
        design,
        wall_thickness_m=0.005,
        external_pressure=pascal(0),
        material_temperature_k=300,
    )
    assert result.status is ResultStatus.CURRENT
    assert result.outputs["material_id"]["value"] == material


def test_unknown_material_never_substitutes() -> None:
    design = structural_design()
    result = run_materials_stage(design, material_id="unknown_alloy")
    assert result.status is ResultStatus.FAILED
    assert result.inputs["material_id"] == "unknown_alloy"
    assert "unknown_alloy" in result.errors[0]["message"]
    assert (
        run_structure_stage(
            design,
            wall_thickness_m=0.005,
            external_pressure=pascal(0),
            material_temperature_k=300,
        ).status
        is ResultStatus.FAILED
    )
    assert design.workflow.current_result("structure") is None
    # A corrupted persisted selection is also rejected by the structural lookup.
    design = structural_design()
    design.material_selection = {"chamber_material_id": "unknown_alloy"}
    result = run_structure_stage(
        design,
        wall_thickness_m=0.005,
        external_pressure=pascal(0),
        material_temperature_k=300,
    )
    assert result.status is ResultStatus.FAILED
    assert result.inputs["material_id"] == "unknown_alloy"
    assert not result.outputs


@pytest.mark.parametrize(
    "missing", ["wall_thickness_m", "external_pressure", "material_temperature_k"]
)
def test_no_hidden_structural_defaults(missing: str) -> None:
    kwargs = {
        "wall_thickness_m": 0.005,
        "external_pressure": pascal(0),
        "material_temperature_k": 300,
    }
    kwargs.pop(missing)
    result = run_structure_stage(structural_design(), **kwargs)
    assert result.status is ResultStatus.FAILED
    assert result.errors[0]["code"] == "InsufficientDataError"


@pytest.mark.parametrize("requirement", list(DependencyRequirement))
@pytest.mark.parametrize(
    "upstream_status",
    [
        ResultStatus.NOT_CALCULATED,
        ResultStatus.STALE,
        ResultStatus.FAILED,
        ResultStatus.NOT_IMPLEMENTED,
        ResultStatus.OUT_OF_RANGE,
    ],
)
def test_dependency_requirement_semantics(
    requirement: DependencyRequirement, upstream_status: ResultStatus
) -> None:
    design = PropulsionDesign(
        name="Dependencies",
        workflow=WorkflowState(
            graph=WorkflowGraph(
                nodes={
                    "upstream": WorkflowNode("upstream", "Upstream"),
                    "downstream": WorkflowNode(
                        "downstream",
                        "Downstream",
                        (StageDependency("upstream", requirement),),
                    ),
                }
            )
        ),
    )
    design.workflow.store_result(
        "upstream", CalculationResult(calculation_type="test", status=upstream_status)
    )
    invoked = []

    @stage_guard("downstream")
    def calculate(design: PropulsionDesign) -> CalculationResult:
        invoked.append(True)
        result = make_result(
            calculation_type="test", stage_id="downstream", status=ResultStatus.CURRENT
        )
        design.store_stage_result("downstream", result)
        return result

    result = calculate(design)
    if requirement is DependencyRequirement.REQUIRED:
        assert not invoked
        assert result.status is ResultStatus.FAILED
        assert design.workflow.current_result("downstream") is None
    else:
        assert invoked
        assert result.status is ResultStatus.CURRENT
        assert result.inputs["dependency_gaps"][0]["requirement"] == requirement.value
        assert result.warnings and result.assumptions


def test_chamber_defaults_fail_closed() -> None:
    design = structural_design()
    design.nozzle_design = {"throat_area_m2": 0.01}
    design.workflow.store_result(
        "performance",
        CalculationResult(calculation_type="performance", status=ResultStatus.CURRENT),
    )
    result = run_chamber_stage(design)
    assert result.status is ResultStatus.FAILED
    assert result.errors[0]["code"] == "InsufficientDataError"


@pytest.mark.parametrize(
    "field,root",
    [
        ("chamber_pressure", "operating_point"),
        ("mixture_ratio", "propellants"),
        ("propellant", "propellants"),
        ("gamma", "operating_point"),
        ("Tc", "operating_point"),
        ("throat_area_m2", "performance"),
        ("expansion_ratio", "requirements"),
        ("material", "materials"),
        ("wall_thickness", "structure"),
        ("external_pressure", "structure"),
    ],
)
def test_input_change_invalidation(field: str, root: str) -> None:
    design = PropulsionDesign(name="Invalidation")
    for sid in design.workflow.graph.nodes:
        design.workflow.store_result(
            sid, CalculationResult(calculation_type=sid, status=ResultStatus.CURRENT)
        )
    marked = design.record_input_change(field, 1, 2)
    assert root in marked
    assert design.workflow.current_result(root) is None
    assert design.workflow.current_result("design_review") is None


def test_typed_edges_roundtrip_and_legacy_migration() -> None:
    state = WorkflowState()
    serialized = state.to_canonical_dict()
    restored = WorkflowState.from_canonical_dict(serialized)
    assert (
        restored.graph.get("chamber").dependencies
        == state.graph.get("chamber").dependencies
    )
    for node in serialized["graph"]["nodes"].values():
        node.pop("dependency_edges")
    restored = WorkflowState.from_canonical_dict(serialized)
    edge = next(
        item
        for item in restored.graph.get("chamber").dependencies
        if item.stage_id == "injector"
    )
    assert edge.requirement is DependencyRequirement.DEFERRED
