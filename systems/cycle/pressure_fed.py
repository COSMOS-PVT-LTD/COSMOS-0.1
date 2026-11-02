"""Read-only pressure-fed assessment; deliberately not an upstream cycle stage."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from core.dimension import MASS_FLOW_RATE, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.feed.pressure_fed import (
    PRESSURE_FED,
    PressureLoss,
    liquid_feed_budget,
    steady_mass_residual,
)
from physics.injectors.orifice import bipropellant_mass_split
from physics.quantities import as_si
from systems.contracts.results import (
    CalculationResult,
    ProvenanceInfo,
    ResultStatus,
    ValidationInfo,
    ValidityInfo,
    ValidityState,
    VerificationInfo,
)
from systems.cycle.models import CycleType
from systems.projects.models import PropulsionDesign

INPUT_SCHEMA = "cosmos.pressure-fed-assessment-input.v1"
OUTPUT_SCHEMA = "cosmos.pressure-fed-assessment.v1"
_LOSSES = {"feed_line", "valves", "cooling"}
_STREAM_FIELDS = {
    "phase",
    "temperature",
    "density",
    "density_source",
    "tank_pressure",
    "tank_pressure_source",
    "tank_mass_flow",
    "tank_mass_flow_source",
    "manifold_area",
    "elevation_rise",
    "injector_static_pressure_drop",
    "injector_source",
    "losses",
}


def _keys(value: Any, fields: set[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise InvalidInputError(
            f"{name} requires exactly: {', '.join(sorted(fields))}."
        )
    return value


def _number(value: Any, name: str) -> float:
    if type(value) not in {float, int}:
        raise InvalidInputError(
            f"{name} must be a finite real number, not Boolean/text."
        )
    try:
        result = float(value)
    except OverflowError as error:
        raise InvalidInputError(f"{name} exceeds finite range.") from error
    if not math.isfinite(result):
        raise InvalidInputError(f"{name} must be finite.")
    return result


def _quantity(
    value: Any, unit: str, name: str, *, signed: bool = False, zero: bool = False
) -> Quantity:
    _keys(value, {"value", "unit"}, name)
    if value["unit"] != unit:
        raise InvalidInputError(
            f"{name} requires explicit SI unit {unit}; no implicit conversion."
        )
    magnitude = _number(value["value"], name)
    if not signed and (magnitude < 0 or (magnitude == 0 and not zero)):
        raise InvalidInputError(f"{name} is outside its declared sign domain.")
    return Quantity(magnitude, SI.get(unit))


def _source(value: Any, name: str) -> None:
    if type(value) is not str or not value.strip() or len(value) > 2048:
        raise InsufficientDataError(
            f"{name} needs an explicit nonempty source/assumption (at most2048 characters)."
        )


def _validate(spec: dict[str, Any]) -> dict[str, Any]:
    _keys(
        spec,
        {
            "schema",
            "regime",
            "pressurant_boundary",
            "flow_accounting",
            "gravity",
            "pressure_tolerance",
            "mass_flow_tolerance",
            "external_oxidizer_outflow",
            "external_fuel_outflow",
            "streams",
        },
        "pressure-fed specification",
    )
    if spec["schema"] != INPUT_SCHEMA:
        raise InvalidInputError("Unsupported pressure-fed assessment input schema.")
    if (
        spec["regime"] != "STEADY_SINGLE_PHASE_INCOMPRESSIBLE"
        or spec["pressurant_boundary"] != "REGULATED_TANK_PRESSURE"
        or spec["flow_accounting"] != "CORE_ONLY_NO_DIVERSION"
    ):
        raise OutOfRangeError(
            "Only steady liquid core-only flow and an imposed regulated tank-pressure boundary are supported."
        )
    values: dict[str, Any] = {
        "gravity": _quantity(spec["gravity"], "m/s2", "gravity", zero=True),
        "pressure_tolerance": _quantity(
            spec["pressure_tolerance"], "Pa", "pressure_tolerance"
        ),
        "mass_flow_tolerance": _quantity(
            spec["mass_flow_tolerance"], "kg/s", "mass_flow_tolerance"
        ),
    }
    for stream in ("oxidizer", "fuel"):
        external = _quantity(
            spec[f"external_{stream}_outflow"],
            "kg/s",
            f"external_{stream}_outflow",
            zero=True,
        )
        if external.to_si() != 0:
            raise OutOfRangeError(
                "Nonzero film/GG/external diversion is not coupled in this core-only model; never assumed zero."
            )
    _keys(spec["streams"], {"oxidizer", "fuel"}, "streams")
    for name, cfg in spec["streams"].items():
        _keys(cfg, _STREAM_FIELDS, name)
        if cfg["phase"] != "LIQUID":
            raise OutOfRangeError(
                "Each stream must explicitly declare single-phase LIQUID; phase is not inferred."
            )
        for key in (
            "density_source",
            "tank_pressure_source",
            "tank_mass_flow_source",
            "injector_source",
        ):
            _source(cfg[key], f"{name}.{key}")
        units = {
            "temperature": "K",
            "density": "kg/m3",
            "tank_pressure": "Pa",
            "tank_mass_flow": "kg/s",
            "manifold_area": "m2",
            "elevation_rise": "m",
            "injector_static_pressure_drop": "Pa",
        }
        parsed: dict[str, Any] = {
            key: _quantity(
                cfg[key], unit, f"{name}.{key}", signed=key == "elevation_rise"
            )
            for key, unit in units.items()
        }
        _keys(cfg["losses"], _LOSSES, f"{name}.losses")
        losses = []
        for label in sorted(_LOSSES):
            loss = cfg["losses"][label]
            _keys(loss, {"pressure_equivalent", "source"}, f"{name}.{label}")
            _source(loss["source"], f"{name}.{label}.source")
            losses.append(
                PressureLoss(
                    label,
                    _quantity(loss["pressure_equivalent"], "Pa", label, zero=True),
                )
            )
        parsed["losses"] = tuple(losses)
        values[name] = parsed
    return values


def _retained_quantity(data: Any, dimension: Any, name: str) -> Quantity:
    if type(data) is not dict:
        raise InsufficientDataError(f"Retained {name} quantity is required.")
    try:
        # The baseline is a trusted canonical DTO but still reject Boolean/NaN
        # magnitudes before the general legacy deserializer can coerce them.
        _number(data["magnitude"], name)
        result = Quantity.from_canonical_dict(data)
        si = as_si(result, dimension, name)
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise InvalidInputError(f"Invalid retained {name} quantity.") from error
    if not math.isfinite(si) or si <= 0:
        raise InvalidInputError(f"Retained {name} must be positive and finite.")
    return result


def assess(
    design: PropulsionDesign, specification: dict[str, Any]
) -> CalculationResult:
    """Capture an exact baseline and return an unattached supplemental result.

    No persistence or authority is inferred. The caller must not store this as
    the upstream cycle stage or interpret CURRENT as full cycle completion.
    """
    if type(specification) is not dict:
        raise InvalidInputError("Pressure-fed specification must be an object.")
    spec = deepcopy(specification)
    values = _validate(spec)
    baseline_text = design.to_canonical_json()
    snapshot = PropulsionDesign.from_canonical_dict(json.loads(baseline_text))
    if snapshot.cycle_configuration.cycle_type is not CycleType.PRESSURE_FED:
        raise OutOfRangeError(
            "Select PRESSURE_FED explicitly; other cycles have no model here."
        )
    captured = {}
    for stage in ("operating_point", "propellants", "thermochemistry", "performance"):
        result = snapshot.workflow.current_result(stage)
        if (
            result is None
            or snapshot.workflow.graph.get(stage).status is not ResultStatus.CURRENT
        ):
            raise InsufficientDataError(
                f"CURRENT retained {stage} result and graph status are required."
            )
        captured[stage] = result
    performance, op = captured["performance"], captured["operating_point"]
    if (
        snapshot.thermochemistry_configuration.get("mode") == "nasa_cea"
        or captured["thermochemistry"].inputs.get("engine") == "nasa/cea"
        or performance.calculation_type != "performance.choked_nozzle_thrust"
    ):
        raise OutOfRangeError(
            "This initial pressure-feed adapter is qualified only for explicit assumed-state performance; no CEA fallback."
        )
    chamber = _retained_quantity(
        performance.inputs.get("chamber_pressure"), PRESSURE, "chamber_pressure"
    )
    op_chamber = _retained_quantity(
        op.outputs.get("chamber_pressure"), PRESSURE, "operating chamber_pressure"
    )
    if chamber.to_si() != op_chamber.to_si():
        raise InvalidInputError(
            "Retained operating-point and performance chamber pressures disagree."
        )
    total = _retained_quantity(
        performance.outputs.get("mass_flow"), MASS_FLOW_RATE, "mass_flow"
    )
    ratio = _number(op.outputs.get("mixture_ratio"), "retained core O/F")
    # These are source identities, not a new propellant registry/property lookup.
    selection = snapshot.propellant_configuration
    propellant_inputs = captured["propellants"].inputs
    propellant_ratio = _keys(
        captured["propellants"].outputs.get("mixture_ratio"),
        {"value", "unit"},
        "retained propellant O/F",
    )
    req = snapshot.requirements
    if (
        ratio <= 0
        or selection.mixture_ratio != ratio
        or not selection.oxidizer_id
        or not selection.fuel_id
        or not snapshot.operating_point.chamber_pressure
        or snapshot.operating_point.chamber_pressure.to_si() != chamber.to_si()
        or snapshot.operating_point.mixture_ratio != ratio
        or propellant_ratio["unit"] != "1"
        or _number(propellant_ratio["value"], "retained propellant O/F") != ratio
        or propellant_inputs.get("mixture_ratio") != ratio
        or propellant_inputs.get("oxidizer_id") != selection.oxidizer_id
        or propellant_inputs.get("fuel_id") != selection.fuel_id
        or req.mixture_ratio != ratio
        or req.cycle_type != CycleType.PRESSURE_FED.value
        or req.target_chamber_pressure is None
        or req.target_chamber_pressure.to_si() != chamber.to_si()
    ):
        raise InvalidInputError(
            "Retained core O/F/Pc or explicit propellant identities are missing/inconsistent."
        )
    core = dict(
        zip(("oxidizer", "fuel"), bipropellant_mass_split(total, ratio), strict=True)
    )
    streams: dict[str, Any] = {}
    mass_tolerance = values["mass_flow_tolerance"].to_si()
    pressure_tolerance = values["pressure_tolerance"].to_si()
    for name, flow in core.items():
        cfg = values[name]
        # Injector static delta-p defines the sink station; it is NOT counted
        # again among irreversible upstream path losses.
        sink = chamber + cfg["injector_static_pressure_drop"]
        budget = liquid_feed_budget(
            mass_flow=flow,
            density=cfg["density"],
            source_pressure=cfg["tank_pressure"],
            required_sink_pressure=sink,
            outlet_area=cfg["manifold_area"],
            source_velocity=Quantity(0, SI.get("m/s")),
            elevation_rise=cfg["elevation_rise"],
            gravitational_acceleration=values["gravity"],
            losses=cfg["losses"],
        )
        residual = steady_mass_residual(
            inlets=(cfg["tank_mass_flow"],), outlets=(flow,)
        )
        state = (
            "DEFICIT"
            if budget.pressure_residual_pa < -pressure_tolerance
            else "SURPLUS_REQUIRES_CONTROL"
            if budget.pressure_residual_pa > pressure_tolerance
            else "BALANCED_WITHIN_TOLERANCE"
        )
        streams[name] = {
            **asdict(budget),
            "propellant_id": getattr(selection, f"{name}_id"),
            "tank_mass_flow_kg_s": cfg["tank_mass_flow"].to_si(),
            "mass_residual_kg_s": residual,
            "mass_matches_core_demand": abs(residual) <= mass_tolerance,
            "pressure_state": state,
        }
    total_residual = steady_mass_residual(
        inlets=tuple(values[name]["tank_mass_flow"] for name in core),
        outlets=tuple(core.values()),
    )
    closed = abs(total_residual) <= mass_tolerance and all(
        row["mass_matches_core_demand"]
        and row["pressure_state"] == "BALANCED_WITHIN_TOLERANCE"
        for row in streams.values()
    )
    return CalculationResult(
        calculation_type="cycle.pressure_fed.supplemental_assessment",
        status=ResultStatus.CURRENT,
        model_id=PRESSURE_FED.model_id,
        model_version=PRESSURE_FED.version,
        stage_id=None,
        design_revision=snapshot.revision,
        inputs={
            "schema": INPUT_SCHEMA,
            "specification": spec,
            "baseline_design_id": snapshot.design_id,
            "baseline_revision": snapshot.revision,
            "baseline_canonical_text": baseline_text,
            "baseline_sha256": sha256(baseline_text.encode()).hexdigest(),
            "source_results": {
                key: result.to_canonical_dict() for key, result in captured.items()
            },
        },
        outputs={
            "schema": OUTPUT_SCHEMA,
            "streams": streams,
            "total_core_mass_flow_kg_s": total.to_si(),
            "total_mass_residual_kg_s": total_residual,
            "assessment_balances_closed_within_declared_tolerances": closed,
            "pressure_tolerance_pa": pressure_tolerance,
            "mass_flow_tolerance_kg_s": mass_tolerance,
            "flow_solution": "NOT_SOLVED_IMPOSED_CORE_FLOW",
            "workflow_cycle_complete": False,
            "cycle_implementation_status": "NOT_IMPLEMENTED",
            "shaft_power": {"status": "NOT_APPLICABLE", "value": None, "unit": "W"},
            "pressurant": {"status": "BOUNDARY_ONLY_CONSUMPTION_AND_WORK_NOT_ASSESSED"},
            "subsystem_coupling": "NOT_ASSESSED_CURRENT_INJECTOR_COOLING_RESULTS_NOT_CONSUMED",
            "physical_validation": "NOT_PERFORMED",
        },
        assumptions=PRESSURE_FED.assumptions
        + (
            "Tank pressure is an imposed regulated boundary; free-surface liquid velocity assumed zero.",
            "Manifold static pressure is Pc plus supplied injector static delta-p; injector is not a second path loss.",
            "Density, phase, temperature and upstream loss data are caller-declared, not independently validated.",
            "No external flow diversion; tank withdrawal is tested independently against required core flow.",
        ),
        warnings=PRESSURE_FED.limitations
        + (
            "Supplemental result only; no managed storage/UI/stage activation or complete cycle qualification.",
            "Declared balance tolerances are not measurement uncertainty, hardware acceptance or a safety margin.",
        ),
        validity=ValidityInfo(
            status=ValidityState.UNKNOWN, valid_range=PRESSURE_FED.validity_range
        ),
        verification=VerificationInfo(
            status="SOFTWARE_VERIFIED", reference=PRESSURE_FED.verification_status
        ),
        validation=ValidationInfo(status="NOT_PERFORMED"),
        provenance=ProvenanceInfo(
            source=PRESSURE_FED.source,
            model=PRESSURE_FED.model_id,
            version=PRESSURE_FED.version,
            calculation_revision=snapshot.revision,
        ),
    )
