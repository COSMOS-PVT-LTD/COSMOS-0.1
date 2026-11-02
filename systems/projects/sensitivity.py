"""Bounded one-at-a-time studies over immutable existing propulsion models.

No engine equations, filesystem IO or authority inferred from browser state.
The composition boundary supplies the unchanged evaluator and source identities.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping
from dataclasses import asdict
from hashlib import sha256
from itertools import pairwise
from typing import Any, cast

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.sensitivity.local import gradient
from physics.exceptions import PhysicsError
from systems.contracts.results import ResultStatus
from systems.persistence.project_repository import (
    Dependency,
    ProjectRepository,
    RecordPayload,
)
from systems.projects.authority import (
    Head,
    HeadConflict,
    IntegrityFailure,
    InvalidRecord,
    Principal,
    SavedSnapshot,
    StoreUnavailable,
    require_active_project,
)
from systems.projects.models import PropulsionDesign
from systems.projects.propulsion_authority import DOMAIN as PROPULSION
from systems.projects.propulsion_authority import (
    PropulsionProjectService,
    decode_design,
)

DOMAIN = "propulsion-sensitivity"
INPUTS = "propulsion-sensitivity-inputs"
SCHEMA = "cosmos.propulsion-sensitivity.v1"
METHOD = "oat-explicit-values+centered-difference-h-and-h/2-v1"
PARAMETERS = {
    "chamber_pressure_pa": ("Chamber pressure", "Pa"),
    "ambient_pressure_pa": ("Ambient pressure", "Pa"),
    "throat_area_m2": ("Throat area", "m2"),
    "expansion_ratio": ("Nozzle expansion ratio", "1"),
}
OUTPUTS = {
    "thrust": ("Calculated thrust", "N"),
    "mass_flow": ("Core mass flow", "kg/s"),
    "specific_impulse": ("Ideal specific impulse", "s"),
    "exit_velocity": ("Exit velocity", "m/s"),
}
Evaluator = Callable[[PropulsionDesign, str, float], dict[str, Any]]


def number(value: object) -> float:
    if type(value) not in {int, float}:
        raise InvalidRecord(
            "Explicit finite real numbers required; Boolean/NaN/infinity are not samples."
        )
    try:
        result = float(cast(int | float, value))
    except OverflowError as error:
        raise InvalidRecord(
            "Sample is outside representable finite real range."
        ) from error
    if not math.isfinite(result):
        raise InvalidRecord(
            "Explicit finite real numbers required; Boolean/NaN/infinity are not samples."
        )
    return result


def validate(spec: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict) or set(spec) != {
        "parameter",
        "unit",
        "values",
        "output",
        "step",
    }:
        raise InvalidRecord(
            "Supply only parameter, SI unit, explicit values, output and absolute SI step."
        )
    parameter, output = spec["parameter"], spec["output"]
    if (
        type(parameter) is not str
        or type(output) is not str
        or parameter not in PARAMETERS
        or output not in OUTPUTS
        or spec["unit"] != PARAMETERS[parameter][1]
    ):
        raise InvalidRecord(
            "Unsupported parameter/output or mismatched SI unit; no implicit conversion/model selection."
        )
    if type(spec["values"]) is not list or not 3 <= len(spec["values"]) <= 21:
        raise InvalidRecord(
            "Supply 3–21 explicit increasing sample values; no hidden/stochastic sampling."
        )
    values = [number(x) for x in spec["values"]]
    if any(a >= b for a, b in pairwise(values)):
        raise InvalidRecord(
            "Sample values must be strictly increasing, without duplicates."
        )
    step = number(spec["step"])
    if step <= 0:
        raise InvalidRecord("A positive absolute SI derivative step is required.")
    return {**spec, "values": values, "step": step}


def baseline_value(design: PropulsionDesign, parameter: str) -> float:
    result = design.workflow.current_result("performance")
    thermo = design.workflow.current_result("thermochemistry")
    if (
        result is None
        or thermo is None
        or design.thermochemistry_configuration.get("mode") == "nasa_cea"
        or thermo.inputs.get("engine") == "nasa/cea"
    ):
        raise InvalidRecord(
            "This first slice requires a current explicit assumed-state performance baseline; CEA sweeps are not yet supported and never fall back to assumptions."
        )
    key = {
        "chamber_pressure_pa": "chamber_pressure",
        "ambient_pressure_pa": "ambient_pressure",
    }.get(parameter, parameter)
    value = result.inputs.get(key)
    if not isinstance(value, dict):
        raise InvalidRecord(
            "The selected performance result does not retain its consumed parameter."
        )
    if parameter in {"chamber_pressure_pa", "ambient_pressure_pa"}:
        from core.quantity import Quantity

        return number(Quantity.from_canonical_dict(value).to_si())
    return number(value.get("value"))


def study(
    baseline: PropulsionDesign, spec: Mapping[str, Any], evaluate: Evaluator
) -> dict[str, Any]:
    spec = validate(spec)
    parameter, output, step = spec["parameter"], spec["output"], spec["step"]
    origin = baseline.to_canonical_dict()
    x0 = baseline_value(baseline, parameter)
    if any(x0 + h == x0 or x0 - h == x0 for h in (step, step / 2)):
        raise InvalidRecord(
            "Derivative step/half-step is below floating-point spacing at this baseline."
        )
    evaluated: dict[float, dict[str, Any]] = {}

    def point(x: float) -> dict[str, Any]:
        if x in evaluated:
            return evaluated[x]
        captured: dict[str, Any] = {}
        try:
            if (
                x < 0
                or (parameter != "ambient_pressure_pa" and x <= 0)
                or (parameter == "expansion_ratio" and x <= 1)
            ):
                raise InvalidInputError(
                    "Sample is outside the declared positive/choked-nozzle parameter domain."
                )
            captured = evaluate(
                PropulsionDesign.from_canonical_dict(origin), parameter, x
            )
            result = captured["performance"]
            if (
                result["status"] != ResultStatus.CURRENT.value
                or result["validity"]["status"] != "VALID"
            ):
                raise InvalidInputError(
                    "Existing model refused this sample: "
                    + json.dumps(result["errors"])
                )
            cell = result["outputs"][output]
            value = number(cell["magnitude"] if "magnitude" in cell else cell["value"])
            row = {"value": x, "status": "EVALUATED", "output": value, **captured}
        except (
            InvalidInputError,
            PhysicsError,
            SolverConvergenceError,
            ArithmeticError,
            ValueError,
            InvalidRecord,
        ) as exc:
            row = {
                **captured,
                "value": x,
                "status": "INVALID_DOMAIN",
                "output": None,
                "error": {"code": type(exc).__name__, "message": str(exc)[:1024]},
            }
        evaluated[x] = row
        return row

    base = point(x0)
    if base["status"] != "EVALUATED":
        raise InvalidRecord(
            "The captured baseline cannot be reproduced by the declared existing model."
        )
    rows = [point(x) for x in spec["values"]]

    def model(state):
        row = point(float(state[0]))
        if row["status"] != "EVALUATED":
            raise InvalidInputError(
                "A centered-difference stencil point is outside the model domain."
            )
        return row["output"]

    derivatives: list[dict[str, Any]] = []
    for h in (step, step / 2):
        # Capture both stencil sides even when the first evaluation is invalid.
        point(x0 - h)
        point(x0 + h)
        try:
            value = number(float(gradient(model, [x0], step=h)[0]))
            derivatives.append({"step": h, "status": "EVALUATED", "value": value})
        except (
            InvalidInputError,
            SolverConvergenceError,
            ArithmeticError,
            ValueError,
        ) as exc:
            derivatives.append(
                {
                    "step": h,
                    "status": "UNAVAILABLE",
                    "value": None,
                    "reason": str(exc)[:1024],
                }
            )
    difference = (
        abs(derivatives[0]["value"] - derivatives[1]["value"])
        if all(d["status"] == "EVALUATED" for d in derivatives)
        else None
    )
    assert baseline.to_canonical_dict() == origin
    return {
        "schema": SCHEMA,
        "method": METHOD,
        "specification": spec,
        "baseline_parameter": x0,
        "baseline_output": base["output"],
        "output_unit": OUTPUTS[output][1],
        "derivative_unit": OUTPUTS[output][1] + "/(" + PARAMETERS[parameter][1] + ")",
        "samples": rows,
        "evaluations": list(evaluated.values()),
        "derivatives": derivatives,
        "step_refinement_absolute_difference": difference,
        "status": "COMPLETED"
        if all(row["status"] == "EVALUATED" for row in rows)
        else "COMPLETED_WITH_INVALID_DOMAINS",
        "uncertainty": "NOT_QUANTIFIED",
        "physical_validation": "NOT_PERFORMED",
        "production_handoff": False,
        "limitations": [
            "One-at-a-time response of the existing preliminary assumed-state nozzle model; not global sensitivity or a closed engine cycle.",
            "h versus h/2 is a step-refinement diagnostic, not an error bound or physical validation.",
            "Invalid samples/stencils are retained; no extrapolation, silent one-sided derivative or gap interpolation.",
        ],
    }


class ManagedSensitivity:
    def __init__(
        self,
        repository: ProjectRepository,
        evaluate: Evaluator,
        methods: Callable[[], dict[str, str]],
    ) -> None:
        self.repository, self.evaluate, self.methods = repository, evaluate, methods
        self.loaded_methods = dict(methods())

    def create(
        self,
        actor: Principal,
        project_id: str,
        baseline_commit: str,
        expected_baseline: Head,
        spec: Mapping[str, Any],
        operation_id: str,
        command_hash: str,
    ) -> SavedSnapshot:
        replay = self.repository.resolve_command(
            actor, project_id, operation_id=operation_id, command_hash=command_hash
        )
        if replay is not None:
            return replay
        require_active_project(self.repository.get_project(actor, project_id))
        source = self.repository.resolve_snapshot(actor, project_id, baseline_commit)
        design = decode_design(source)
        current = self.repository.get_snapshot(
            actor, project_id, domain=PROPULSION, object_id=source.object_id
        )
        if source.commit_id != current.commit_id or current.head != expected_baseline:
            raise HeadConflict(current.head)
        spec = validate(spec)
        baseline_value(design, spec["parameter"])
        methods = self.methods()
        if methods != self.loaded_methods:
            raise StoreUnavailable(
                "Scientific sources changed since this application was composed. Restart before starting a new sensitivity study."
            )
        object_id = PropulsionProjectService.new_id(
            actor, project_id, operation_id, "sensitivity"
        )
        capture = {
            "baseline_commit_id": source.commit_id,
            "baseline_sha256": source.head.content_hash,
            "baseline_canonical_json": source.payload.decode(),
            "method_sources": methods,
            "specification": spec,
        }
        inputs = self.repository.save_snapshot(
            actor,
            project_id,
            domain=INPUTS,
            object_id=object_id,
            input_revision=source.input_revision,
            payload=RecordPayload.from_mapping(
                capture, "cosmos.propulsion-sensitivity-input.v1"
            ),
            expected=Head.absent(),
            operation_id="sensitivity-input."
            + sha256((actor.user_id + operation_id).encode()).hexdigest(),
            command_hash=sha256((command_hash + ":inputs").encode()).hexdigest(),
            dependencies=(Dependency("baseline", source.commit_id),),
        )
        result = study(design, spec, self.evaluate)
        if self.methods() != methods:
            raise IntegrityFailure(
                "Model sources changed during analysis; retained inputs remain but no result was published."
            )
        return self.repository.save_snapshot(
            actor,
            project_id,
            domain=DOMAIN,
            object_id=object_id,
            input_revision=source.input_revision,
            payload=RecordPayload.from_mapping({**capture, **result}, SCHEMA),
            expected=Head.absent(),
            operation_id=operation_id,
            command_hash=command_hash,
            input_commit_id=inputs.commit_id,
            dependencies=(
                Dependency("baseline", source.commit_id),
                Dependency("captured-inputs", inputs.commit_id),
            ),
        )

    def read(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        if source.domain != DOMAIN or source.schema_id != SCHEMA:
            raise InvalidRecord("Not a supported sensitivity record.")
        value = json.loads(source.payload)
        return {
            "ok": True,
            "authority": {
                "project_id": source.project_id,
                "object_id": source.object_id,
                "commit_id": source.commit_id,
                "head": asdict(source.head),
                "input_revision": source.input_revision,
            },
            "record": value,
            "source_canonical_json": source.payload.decode(),
            "upstream_current": self.repository.dependencies_current(
                actor, source.project_id, source.commit_id
            )
            and value["method_sources"] == self.loaded_methods == self.methods(),
        }
