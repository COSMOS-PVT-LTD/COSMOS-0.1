"""Bounded, exact-recipe local sensitivity; reuse the coupled operating solver."""

from __future__ import annotations

import math
from collections.abc import Callable
from copy import deepcopy
from itertools import pairwise
from time import monotonic
from typing import Any

from core.exceptions import CosmosError, InvalidInputError
from numerics.sensitivity.local import gradient
from systems.contracts.results import CalculationResult, ResultStatus, ValidationInfo
from systems.cycle.engine_operating import assess
from systems.cycle.operating_contract import scalar
from systems.cycle.operating_contract import validate as validate_recipe
from systems.cycle.pressure_fed import _keys, _source
from systems.cycle.pressure_fed import _number as number
from systems.projects.models import PropulsionDesign

SCHEMA = "cosmos.operating-sensitivity-input.v1"
METHOD = "coupled-operating-oat-centered-h-and-h2-v1"
PARAMETERS = {
    **{f"feeds.{name}.{key}": (f"{name} {key}", unit)
       for name in ("oxidizer", "fuel")
       for key, unit in (("tank_pressure", "Pa"), ("core_resistance", "Pa*s2/kg2"), ("temperature", "K"))},
    **{f"feeds.{name}.pump.{key}": (f"{name} pump {key}", unit)
       for name in ("oxidizer", "fuel")
       for key, unit in (("speed_coefficient", "Pa*s2/rad2"), ("flow_coefficient", "Pa*s2/kg2"))},
    "gas_generator.throat_area": ("Gas-generator effective throat area", "m2"),
}
OUTPUTS = {
    "core.thrust_n": ("Core thrust", "N"),
    "core.mass_flow_kg_s": ("Core mass flow", "kg/s"),
    "core.mixture_ratio": ("Core O/F", "1"),
    "core.gas.temperature_k": ("HP chamber temperature", "K"),
    "unknowns.chamber_pressure.value": ("Solved chamber pressure", "Pa"),
    "unknowns.shaft_speed.value": ("Solved GG shaft speed", "rad/s"),
    "cooling.total_heat_w": ("Regenerative heat pickup", "W"),
    "cooling.outlet_temperature_k": ("Coolant return temperature", "K"),
}


def at_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise InvalidInputError(f"{path} is unavailable in this selected model; no fallback.")
        current = current[key]
    return current


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    _keys(spec, {"schema", "recipe", "parameter", "unit", "values", "output", "step", "max_seconds", "source"}, "operating sensitivity")
    if spec["schema"] != SCHEMA or spec["parameter"] not in PARAMETERS or spec["output"] not in OUTPUTS:
        raise InvalidInputError("Select a supported operating sensitivity parameter/output/schema.")
    validate_recipe(spec["recipe"])
    unit = PARAMETERS[spec["parameter"]][1]
    if spec["unit"] != unit:
        raise InvalidInputError("Sensitivity requires the declared explicit SI input unit.")
    _source(spec["source"], "sample range/step purpose and applicability")
    raw = spec["values"]
    if not isinstance(raw, list) or not 3 <= len(raw) <= 5:
        raise InvalidInputError("Supply 3–5 explicit increasing unique samples; at most 10 distinct solves including stencil.")
    values = [number(v, "sample") for v in raw]
    if any(b <= a for a, b in pairwise(values)):
        raise InvalidInputError("Samples must be increasing and unique.")
    x0 = number(at_path(spec["recipe"], spec["parameter"])["value"], "recipe parameter")
    step = scalar(spec["step"], unit, "centered difference step")
    if not values[0] <= x0 <= values[-1]:
        raise InvalidInputError("Explicit sample interval must contain the recipe baseline.")
    if any(x0 + d == x0 or not math.isfinite(x0 + d) for d in (-step, step, -step / 2, step / 2)):
        raise InvalidInputError("Centered h and h/2 must be finite and distinct at baseline precision.")
    budget = scalar(spec["max_seconds"], "s", "study admission budget")
    if budget > 120:
        raise InvalidInputError("Study admission budget cannot exceed 120 seconds; a running solve keeps its declared bounded policy.")
    return {"values": values, "baseline": x0, "step": step, "budget": budget}


def study(
    design: PropulsionDesign, specification: dict[str, Any], *,
    evaluator: Callable[[PropulsionDesign, dict[str, Any]], CalculationResult] = assess,
    clock: Callable[[], float] = monotonic,
) -> CalculationResult:
    cfg = validate(specification)
    original = design.to_canonical_json()
    recipe = deepcopy(specification["recipe"])
    started = clock()
    cache: dict[float, dict[str, Any]] = {}

    def evaluate(x: float) -> dict[str, Any]:
        if x in cache:
            return cache[x]
        case = deepcopy(recipe)
        at_path(case, specification["parameter"])["value"] = x
        row: dict[str, Any] = {"value": x, "status": "INVALID", "output": None, "error": None, "result": None, "specification": case}
        try:
            if clock() - started >= cfg["budget"]:
                raise InvalidInputError("Study admission budget exhausted; no new solve admitted. Earlier originals retained.")
            clone = PropulsionDesign.from_canonical_dict(deepcopy(design.to_canonical_dict()))
            result = evaluator(clone, case)
            if clone.to_canonical_json() != original:
                raise InvalidInputError("Case evaluator mutated its immutable baseline copy.")
            row["result"] = result.to_canonical_dict()
            if not result.outputs["solved_candidate_usable"]:
                raise InvalidInputError("No accepted solved candidate: " + result.outputs["termination_reason"])
            row["output"] = number(at_path(result.outputs["candidate"], specification["output"]), "sensitivity output")
            row["status"] = "VALID"
        except (CosmosError, ValueError, ArithmeticError) as error:
            row["error"] = {"code": type(error).__name__, "message": str(error)[:1024]}
        cache[x] = row
        return row

    baseline = evaluate(cfg["baseline"])
    derivatives = []
    for h in (cfg["step"], cfg["step"] / 2):
        # Retain both sides even if the first is invalid; never substitute an
        # invented zero, last accepted state or one-sided derivative.
        sides = [evaluate(cfg["baseline"] - h), evaluate(cfg["baseline"] + h)]
        valid = baseline["status"] == "VALID" and all(row["status"] == "VALID" for row in sides)
        derivative = float(gradient(lambda point: evaluate(float(point[0]))["output"], [cfg["baseline"]], step=h)[0]) if valid else None
        derivatives.append({"step": h, "value": derivative, "status": "AVAILABLE" if valid else "UNAVAILABLE_INVALID_STENCIL"})
    samples = [evaluate(x) for x in cfg["values"]]
    complete = all(row["status"] == "VALID" for row in cache.values())
    diff = abs(derivatives[0]["value"] - derivatives[1]["value"]) if all(d["value"] is not None for d in derivatives) else None
    out_unit = OUTPUTS[specification["output"]][1]
    return CalculationResult(
        calculation_type="cycle.operating_sensitivity", status=ResultStatus.CURRENT,
        model_id=METHOD, model_version="1",
        inputs={"baseline_canonical_text": original, "specification": deepcopy(specification)},
        outputs={"workflow_cycle_complete": False, "study_status": "COMPLETED" if complete else "COMPLETED_WITH_INVALID_DOMAINS", "baseline_value": cfg["baseline"], "baseline_output": baseline["output"], "samples": samples, "evaluations": list(cache.values()), "derivatives": derivatives, "step_refinement_absolute_difference": diff, "derivative_unit": out_unit + "/(" + specification["unit"] + ")", "output_unit": out_unit, "uncertainty": "NOT_QUANTIFIED", "physical_validation": "NOT_PERFORMED", "residuals": []},
        assumptions=("One parameter varied; all other recipe and baseline inputs fixed. Each case independently solves CEA HP, feed and the selected thermal model.",),
        warnings=("h versus h/2 difference is a diagnostic, not an error bound or propagated uncertainty. No interpolation across invalid cases.", "Admission budget is checked between bounded solves, not native process cancellation."),
        validation=ValidationInfo(status="NOT_PERFORMED"),
    )
