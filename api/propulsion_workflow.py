"""
Application API boundary for propulsion workflow (GUI → Systems).

No engineering equations live here — DTO mapping and service calls only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.exceptions import CosmosError, InvalidInputError, UnitError
from core.quantity import Quantity
from core.unit import SI, Unit
from physics.exceptions import OutOfRangeError, PhysicsError

from systems.calculations.isentropic import evaluate_isentropic_stagnation
from systems.contracts.results import CalculationResult, is_current_displayable
from systems.cycle.models import CycleConfiguration, CycleType
from systems.export.design_package import build_design_export_package
from systems.persistence.design_store import DesignStore
from systems.projects.models import PropulsionDesign
from systems.workflow.orchestrator import (
    run_phase3_chain,
    run_phase4_chain,
    run_phase6_chain,
)

__all__ = (
    "create_design",
    "export_design",
    "get_design_payload",
    "get_stage_result_payload",
    "get_workflow_payload",
    "load_design",
    "map_systems_error",
    "run_isentropic",
    "run_phase3",
    "run_phase4",
    "run_phase6",
    "save_design",
    "set_operating_gamma",
    "update_requirements",
)


def _quantity_si(value: float, unit_symbol: str) -> Quantity:
    unit: Unit = SI.get(unit_symbol)
    return Quantity(float(value), unit)


def create_design(
    *,
    name: str,
    description: str = "",
    engineer: str | None = None,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    design = PropulsionDesign(name=name, description=description, engineer=engineer)
    design.cycle_configuration = CycleConfiguration.for_type(CycleType.UNSPECIFIED)
    # Mark design_project / requirements nodes as partial CURRENT scaffolding.
    from systems.contracts.results import ResultStatus

    design.workflow.graph.get("design_project").status = ResultStatus.CURRENT
    design.workflow.graph.get("requirements").status = ResultStatus.NOT_CALCULATED
    if store is not None:
        store.save(design)
    return design


def save_design(design: PropulsionDesign, store: DesignStore) -> Path:
    return store.save(design)


def load_design(design_id: str, store: DesignStore) -> PropulsionDesign:
    return store.load(design_id)


def update_requirements(
    design: PropulsionDesign,
    updates: dict[str, Any],
    *,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    """
    Apply requirement updates. Quantity fields accept {magnitude, unit_symbol}
    with SI symbols (Pa, K, m, s, N) or bare floats interpreted as SI.
    """

    req = design.requirements
    quantity_fields = {
        "target_thrust": "N",
        "ambient_pressure": "Pa",
        "ambient_temperature": "K",
        "operating_altitude": "m",
        "burn_duration": "s",
        "target_chamber_pressure": "Pa",
    }
    for key, value in updates.items():
        old = getattr(req, key, None)
        if key in quantity_fields:
            if value is None:
                new_value = None
            elif isinstance(value, Quantity) or (
                hasattr(value, "to_si") and hasattr(value, "unit")
            ):
                new_value = value  # type: ignore[assignment]
            elif isinstance(value, dict) and "magnitude" in value:
                # Accept either SI symbol shortcut or full Core unit dict.
                if isinstance(value.get("magnitude"), (int, float)):
                    symbol = str(value.get("unit_symbol") or quantity_fields[key])
                    if "unit" in value and isinstance(value["unit"], dict):
                        new_value = Quantity.from_canonical_dict(value)
                    else:
                        new_value = _quantity_si(float(value["magnitude"]), symbol)
                else:
                    raise InvalidInputError(f"Invalid quantity payload for {key!r}.")
            else:
                new_value = _quantity_si(float(value), quantity_fields[key])
            setattr(req, key, new_value)
            design.record_input_change(key, _serialize_value(old), _serialize_value(new_value))
        elif key in {"mixture_ratio", "expansion_ratio"}:
            new_value = None if value is None else float(value)
            setattr(req, key, new_value)
            design.record_input_change(key, old, new_value)
        elif key in {"cycle_type", "propellant_selection", "notes"}:
            new_value = None if value is None else str(value)
            setattr(req, key, new_value)
            design.record_input_change(key, old, new_value)
        else:
            raise InvalidInputError(f"Unknown requirements field: {key!r}.")
    if store is not None:
        store.save(design)
    return design


def set_operating_gamma(
    design: PropulsionDesign,
    gamma: float,
    *,
    as_assumption: bool = True,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    old = design.operating_point.gamma
    design.operating_point.gamma = float(gamma)
    design.operating_point.gamma_is_assumption = bool(as_assumption)
    design.record_input_change("gamma", old, float(gamma))
    if store is not None:
        store.save(design)
    return design


def run_isentropic(
    design: PropulsionDesign,
    *,
    mach: float,
    gamma: float | None = None,
    store: DesignStore | None = None,
) -> CalculationResult:
    result = evaluate_isentropic_stagnation(design, mach=mach, gamma=gamma)
    if store is not None:
        store.save(design)
    return result


def run_phase3(
    design: PropulsionDesign,
    *,
    chamber_temperature_k: float | None = None,
    gamma: float | None = None,
    molecular_weight_kg_per_mol: float | None = None,
    throat_area_m2: float | None = None,
    expansion_ratio: float | None = None,
    store: DesignStore | None = None,
) -> dict[str, object]:
    """Run Requirements→…→Performance chain; return serializable summary."""

    outcome = run_phase3_chain(
        design,
        chamber_temperature_k=chamber_temperature_k,
        gamma=gamma,
        molecular_weight_kg_per_mol=molecular_weight_kg_per_mol,
        throat_area_m2=throat_area_m2,
        expansion_ratio=expansion_ratio,
    )
    if store is not None:
        store.save(design)
    return {
        "ok": outcome.ok,
        "design_id": design.design_id,
        "revision": design.revision,
        "stages": {
            key: value.to_canonical_dict() for key, value in outcome.stages.items()
        },
        "workflow": get_workflow_payload(design),
    }


def run_phase4(
    design: PropulsionDesign,
    *,
    characteristic_length_m: float | None = None,
    contraction_ratio: float | None = None,
    wall_thickness_m: float | None = None,
    material_id: str = "stainless_304",
    store: DesignStore | None = None,
) -> dict[str, object]:
    outcome = run_phase4_chain(
        design,
        characteristic_length_m=characteristic_length_m,
        contraction_ratio=contraction_ratio,
        wall_thickness_m=wall_thickness_m,
        material_id=material_id,
    )
    if store is not None:
        store.save(design)
    return {
        "ok": outcome.ok,
        "design_id": design.design_id,
        "revision": design.revision,
        "stages": {
            key: value.to_canonical_dict() for key, value in outcome.stages.items()
        },
        "workflow": get_workflow_payload(design),
    }


def run_phase6(
    design: PropulsionDesign,
    *,
    store: DesignStore | None = None,
) -> dict[str, object]:
    """Run Performance Summary → Consistency → Design Review."""

    outcome = run_phase6_chain(design)
    if store is not None:
        store.save(design)
    return {
        "ok": outcome.ok,
        "design_id": design.design_id,
        "revision": design.revision,
        "stages": {
            key: value.to_canonical_dict() for key, value in outcome.stages.items()
        },
        "workflow": get_workflow_payload(design),
    }


def export_design(design: PropulsionDesign) -> dict[str, object]:
    """Return export package (JSON-serializable) for download/archive."""

    return build_design_export_package(design)


def get_stage_result_payload(
    design: PropulsionDesign,
    stage_id: str,
    *,
    allow_stale: bool = False,
) -> dict[str, object]:
    """
    Return a stage result. By default only CURRENT is returned as displayable.

    If allow_stale=True, returns the stored envelope with an explicit flag.
    """

    stored = design.workflow.results.get(stage_id)
    if stored is None:
        raise KeyError(stage_id)
    current = design.workflow.current_result(stage_id)
    if current is not None:
        return {
            "ok": True,
            "displayable_as_current": True,
            "result": current.to_canonical_dict(),
        }
    if allow_stale:
        return {
            "ok": True,
            "displayable_as_current": False,
            "result": stored.to_canonical_dict(),
        }
    return {
        "ok": False,
        "displayable_as_current": False,
        "status": stored.status.value,
        "message": (
            f"Stage {stage_id!r} result status is {stored.status.value}; "
            "only CURRENT may be displayed as the active answer."
        ),
        "result": stored.to_canonical_dict(),
    }


def get_design_payload(design: PropulsionDesign) -> dict[str, object]:
    return design.to_canonical_dict()


def get_workflow_payload(design: PropulsionDesign) -> dict[str, object]:
    nodes = []
    for stage_id, node in sorted(design.workflow.graph.nodes.items()):
        result = design.workflow.results.get(stage_id)
        display_status = node.status.value
        current = design.workflow.current_result(stage_id)
        nodes.append(
            {
                "stage_id": stage_id,
                "name": node.name,
                "dependencies": list(node.dependencies),
                "implementation_status": node.implementation_status.value,
                "status": display_status,
                "has_current_result": current is not None,
                "result_id": None if result is None else result.result_id,
                "result_is_current": (
                    False if result is None else is_current_displayable(result.status)
                ),
            }
        )
    return {"design_id": design.design_id, "revision": design.revision, "nodes": nodes}


def map_systems_error(exc: BaseException) -> tuple[int, dict[str, object]]:
    if isinstance(exc, (InvalidInputError, UnitError, ValueError, TypeError, KeyError)):
        status = 400
        code = type(exc).__name__
        message = str(exc) if not isinstance(exc, KeyError) else f"Missing field: {exc.args[0]!r}"
    elif isinstance(exc, OutOfRangeError):
        status = 422
        code = "OutOfRangeError"
        message = str(exc)
    elif isinstance(exc, (PhysicsError, CosmosError)):
        status = 400
        code = type(exc).__name__
        message = str(exc)
    else:
        status = 500
        code = "InternalError"
        message = str(exc)
    return status, {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "action": "Correct the input or select a valid model range.",
        },
    }


def _serialize_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, Quantity):
        return value.to_canonical_dict()
    return value
