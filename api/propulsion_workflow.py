"""
Application API boundary for propulsion workflow (GUI → Systems).

No engineering equations live here — DTO mapping and service calls only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

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
from systems.workflow.graph import (
    BYPASSABLE_WHEN_UNIMPLEMENTED,
    STAGE_ENGINEERING_NOTES,
    ordered_stage_ids,
    stage_index,
)
from systems.workflow.orchestrator import (
    Phase3Result,
    run_phase3_chain,
    run_phase4_chain,
    run_phase6_chain,
)
from systems.workflow.readiness import dependency_assessment, readiness_payload

__all__ = (
    "clone_design",
    "create_design",
    "export_design",
    "get_design_payload",
    "get_stage_result_payload",
    "get_workflow_payload",
    "list_designs",
    "load_design",
    "map_systems_error",
    "run_isentropic",
    "run_phase3",
    "run_phase4",
    "run_phase6",
    "save_design",
    "set_operating_gamma",
    "update_cycle",
    "update_propellants",
    "update_requirements",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _quantity_si(value: float, unit_symbol: str) -> Quantity:
    unit: Unit = SI.get(unit_symbol)
    return Quantity(float(value), unit)


def _phase_payload(outcome: Phase3Result) -> dict[str, object]:
    return {
        "ok": outcome.ok,
        "ok_semantics": "Deprecated alias of execution_ok; does not claim workflow completeness or validation.",
        "execution_ok": outcome.execution_ok,
        **outcome.readiness,
        "phase_status": outcome.phase_status,
        "design_id": outcome.design.design_id,
        "revision": outcome.design.revision,
        "stages": {
            key: value.to_canonical_dict() for key, value in outcome.stages.items()
        },
        "workflow": get_workflow_payload(outcome.design),
        "default_assumptions": _collect_default_assumptions(outcome.stages),
    }


def _collect_default_assumptions(
    stages: dict[str, CalculationResult],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for stage_id, result in stages.items():
        used = result.inputs.get("used_defaults")
        if isinstance(used, dict):
            for field, flag in used.items():
                if flag:
                    rows.append(
                        {
                            "stage_id": stage_id,
                            "field": field,
                            "source": "ASSUMPTION",
                            "reason": "Default applied because the user did not supply a value.",
                        }
                    )
        for assumption in result.assumptions:
            text = str(assumption)
            if "default" in text.lower() or "ASSUMED" in text.upper():
                rows.append(
                    {
                        "stage_id": stage_id,
                        "field": None,
                        "source": "ASSUMPTION",
                        "reason": text,
                    }
                )
    return rows


def create_design(
    *,
    name: str,
    description: str = "",
    engineer: str | None = None,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    design = PropulsionDesign(name=name, description=description, engineer=engineer)
    design.cycle_configuration = CycleConfiguration.for_type(CycleType.UNSPECIFIED)
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


def list_designs(store: DesignStore) -> list[dict[str, object]]:
    return store.list_summaries()


def clone_design(
    design: PropulsionDesign,
    *,
    name: str | None = None,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    data = design.to_canonical_dict()
    cloned = PropulsionDesign.from_canonical_dict(data)
    cloned.design_id = str(uuid4())
    cloned.name = name or f"{design.name} (copy)"
    cloned.revision = 0
    cloned.created_at = _utc_now_iso()
    cloned.updated_at = cloned.created_at
    cloned.change_log = []
    if store is not None:
        store.save(cloned)
    return cloned


def update_requirements(
    design: PropulsionDesign,
    updates: dict[str, Any],
    *,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    """
    Apply requirement updates. Quantity fields accept {magnitude, unit_symbol}
    with Core registry symbols (Pa, kPa, MPa, bar, N, kN, m, mm, K, s) or
    bare floats interpreted as SI.
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


def update_propellants(
    design: PropulsionDesign,
    *,
    oxidizer_id: str,
    fuel_id: str,
    mixture_ratio: float | None = None,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    """Store Physics registry IDs. Display pairs are derived, never authoritative."""

    from api.catalogs import ensure_propellant_registry
    from physics.thermochemistry.propellants import get_propellant_by_alias

    ensure_propellant_registry()
    oxidizer = get_propellant_by_alias(str(oxidizer_id))
    fuel = get_propellant_by_alias(str(fuel_id))
    cfg = design.propellant_configuration
    old = cfg.to_canonical_dict()
    cfg.oxidizer_id = oxidizer.short_name
    cfg.fuel_id = fuel.short_name
    if mixture_ratio is not None:
        cfg.mixture_ratio = float(mixture_ratio)
        design.requirements.mixture_ratio = float(mixture_ratio)
    design.record_input_change("propellant_configuration", old, cfg.to_canonical_dict())
    if store is not None:
        store.save(design)
    return design


def update_cycle(
    design: PropulsionDesign,
    cycle_type: str,
    *,
    store: DesignStore | None = None,
) -> PropulsionDesign:
    """Record cycle class. All cycle types remain NOT_IMPLEMENTED in this foundation."""

    try:
        enum_type = CycleType(str(cycle_type))
    except ValueError as exc:
        raise InvalidInputError(f"Unknown cycle type: {cycle_type!r}.") from exc
    old = design.cycle_configuration.to_canonical_dict()
    design.cycle_configuration = CycleConfiguration.for_type(enum_type)
    design.requirements.cycle_type = enum_type.value
    design.record_input_change("cycle_configuration", old, design.cycle_configuration.to_canonical_dict())
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
    return _phase_payload(outcome)


def run_phase4(
    design: PropulsionDesign,
    *,
    characteristic_length_m: float | None = None,
    contraction_ratio: float | None = None,
    wall_thickness_m: float | None = None,
    material_id: str | None = None,
    external_pressure_pa: float | Quantity | None = None,
    external_pressure_source: str | None = None,
    material_temperature_k: float | None = None,
    viscosity_pa_s: float | None = None,
    conductivity_w_m_k: float | None = None,
    cp_j_kg_k: float | None = None,
    wall_temperature_k: float | None = None,
    throat_curvature_radius_m: float | None = None,
    store: DesignStore | None = None,
) -> dict[str, object]:
    outcome = run_phase4_chain(
        design,
        characteristic_length_m=characteristic_length_m,
        contraction_ratio=contraction_ratio,
        wall_thickness_m=wall_thickness_m,
        material_id=material_id,
        external_pressure=(external_pressure_pa if isinstance(external_pressure_pa, Quantity)
            else None if external_pressure_pa is None else _quantity_si(external_pressure_pa, "Pa")),
        external_pressure_source=external_pressure_source,
        material_temperature_k=material_temperature_k,
        viscosity_pa_s=viscosity_pa_s,
        conductivity_w_m_k=conductivity_w_m_k,
        cp_j_kg_k=cp_j_kg_k,
        wall_temperature_k=wall_temperature_k,
        throat_curvature_radius_m=throat_curvature_radius_m,
    )
    if store is not None:
        store.save(design)
    return _phase_payload(outcome)


def run_phase6(
    design: PropulsionDesign,
    *,
    store: DesignStore | None = None,
) -> dict[str, object]:
    """Run Performance Summary → Consistency → Design Review."""

    outcome = run_phase6_chain(design)
    if store is not None:
        store.save(design)
    return _phase_payload(outcome)


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
    for stage_id in ordered_stage_ids(design.workflow.graph.nodes):
        node = design.workflow.graph.nodes[stage_id]
        result = design.workflow.results.get(stage_id)
        display_status = node.status.value
        current = design.workflow.current_result(stage_id)
        bypass = [
            {"upstream": upstream, "reason": reason}
            for (downstream, upstream), reason in BYPASSABLE_WHEN_UNIMPLEMENTED.items()
            if downstream == stage_id
        ]
        nodes.append(
            {
                "stage_index": stage_index(stage_id),
                "stage_id": stage_id,
                "name": node.name,
                "dependencies": [edge.stage_id for edge in node.dependencies],
                "dependency_edges": dependency_assessment(design.workflow, stage_id),
                "implementation_status": node.implementation_status.value,
                "status": display_status,
                "has_current_result": current is not None,
                "result_id": None if result is None else result.result_id,
                "result_is_current": (
                    False if result is None else is_current_displayable(result.status)
                ),
                "dependency_policy": bypass,
                "engineering_note": STAGE_ENGINEERING_NOTES.get(stage_id, ""),
            }
        )
    return {"design_id": design.design_id, "revision": design.revision, "nodes": nodes, **readiness_payload(design.workflow)}


def map_systems_error(exc: BaseException) -> tuple[int, dict[str, object]]:
    from physics.thermochemistry.propellants import PropellantNotFoundError

    if isinstance(exc, (InvalidInputError, UnitError, ValueError, TypeError, KeyError, PropellantNotFoundError)):
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
