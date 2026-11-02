"""Deterministic six-decision brief and explicit review contract (GD-00/01)."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from hashlib import sha256

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI

PROFILE_ID = "methalox-pf-preliminary-v1"
BRIEF_FIELDS = {
    "thrust",
    "propellants",
    "chamber_pressure",
    "environment",
    "burn_duration",
    "cycle",
}


def digest(value):
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def exact(value, keys, name):
    if type(value) is not dict or set(value) != set(keys):
        raise InvalidInputError(
            f"{name} requires exactly {', '.join(sorted(keys))}; paths, scripts and result overrides are not accepted."
        )


def scalar(value, unit, name, *, minimum=0.0, maximum=1e9, zero=False):
    exact(value, {"value", "unit"}, name)
    number = value["value"]
    if (
        value["unit"] != unit
        or type(number) not in (int, float)
        or not math.isfinite(number)
        or number < minimum
        or (not zero and number == 0)
        or number > maximum
    ):
        raise InvalidInputError(
            f"{name} requires finite {unit} in {minimum}..{maximum} (zero allowed: {zero})."
        )
    # Core validates the declared physical unit; retain original JSON precision.
    Quantity(number, SI.get(unit))
    return number


def brief(value):
    exact(value, BRIEF_FIELDS, "Engine brief")
    scalar(value["thrust"], "N", "Target thrust", maximum=1e6)
    pc = scalar(
        value["chamber_pressure"],
        "Pa",
        "Absolute chamber pressure",
        minimum=2e5,
        maximum=5e6,
    )
    if value["propellants"] != {"fuel": "LCH4", "oxidizer": "LOX"}:
        raise InvalidInputError(
            "Guided profile currently covers LCH4/LOX only. Other combinations remain available through explicit Expert Mode where supported."
        )
    if value["cycle"] != "PRESSURE_FED":
        raise InvalidInputError(
            "Guided automation currently covers pressure-fed only; no cycle substitution is permitted."
        )
    env = value["environment"]
    if type(env) is not dict or env.get("kind") not in {
        "SEA_LEVEL_STANDARD",
        "VACUUM",
        "CUSTOM",
    }:
        raise InvalidInputError(
            "Choose standard sea level, vacuum or custom absolute ambient pressure."
        )
    exact(
        env,
        {"kind", "pressure"} if env["kind"] == "CUSTOM" else {"kind"},
        "Environment",
    )
    pa = (
        101325.0
        if env["kind"] == "SEA_LEVEL_STANDARD"
        else 0.0
        if env["kind"] == "VACUUM"
        else scalar(env["pressure"], "Pa", "Ambient pressure", zero=True)
    )
    if pc <= 2.5 * pa:
        raise InvalidInputError(
            "This guided ideal supersonic profile requires Pc > 2.5 × ambient pressure. Lower ratios need a separately scoped flow regime."
        )
    if value["burn_duration"] is not None:
        scalar(value["burn_duration"], "s", "Burn duration", maximum=3600)
    return deepcopy(value), pa


# These are explicitly provisional design choices, not database measurements.
# Each value is shown in the review and is only used after the exact review hash
# is accepted. Historical study approval is never imported as new approval.
RULES = {
    "fuel_temperature": (
        111.15,
        "K",
        111.15,
        111.15,
        "PROVISIONAL_ASSUMPTION",
        "Named cryogenic inlet assumption; not measured tank or heated-injector state.",
    ),
    "oxidizer_temperature": (
        90.15,
        "K",
        90.15,
        90.15,
        "PROVISIONAL_ASSUMPTION",
        "Named cryogenic inlet assumption; verify actual inlet state.",
    ),
    "characteristic_length": (
        0.8,
        "m",
        0.1,
        3,
        "PROVISIONAL_ASSUMPTION",
        "L* concept choice; no residence-time or stability qualification.",
    ),
    "contraction_ratio": (
        3.0,
        "1",
        1.1,
        10,
        "PROVISIONAL_ASSUMPTION",
        "Cylindrical chamber sizing; convergent and injector volume excluded.",
    ),
    "nozzle_length_fraction": (
        0.8,
        "1",
        0.6,
        1,
        "PROVISIONAL_ASSUMPTION",
        "Existing tangent-bell model, not a Rao/MOC optimum.",
    ),
    "nozzle_start_angle": (
        30.0,
        "deg",
        15,
        40,
        "PROVISIONAL_ASSUMPTION",
        "Provisional tangent-bell start angle, not an optimized contour.",
    ),
    "nozzle_exit_angle": (
        8.0,
        "deg",
        1,
        15,
        "PROVISIONAL_ASSUMPTION",
        "Provisional tangent-bell exit angle.",
    ),
    "nozzle_blend_radius_ratio": (
        0.2,
        "1",
        0.1,
        0.5,
        "PROVISIONAL_ASSUMPTION",
        "Divergent blend radius divided by throat radius.",
    ),
    "nozzle_point_count": (
        41,
        "1",
        11,
        129,
        "CORRELATION_RULE",
        "Bounded source-station resolution, not a manufacturing tolerance.",
    ),
    "injector_cd": (
        0.70,
        "1",
        0.1,
        1,
        "PROVISIONAL_ASSUMPTION",
        "Exploratory Cd, not a measured injector coefficient.",
    ),
    "injector_holes": (
        8,
        "1",
        1,
        256,
        "PROVISIONAL_ASSUMPTION",
        "Identical cold circular holes per propellant; atomization/stability not assessed.",
    ),
    "injector_pressure_drop": (
        100000.0,
        "Pa",
        10000,
        2e6,
        "PROVISIONAL_ASSUMPTION",
        "Cold hydraulic sizing pressure drop, not a validated stability requirement.",
    ),
    "regulated_feed_pressure": (
        800000.0,
        "Pa",
        2e5,
        1e7,
        "PROVISIONAL_ASSUMPTION",
        "Proposed available regulated pressure for budget screening; not actual tank capability.",
    ),
}
LOCKS = {
    "mixture_ratio": ("1", 1.5, 4.5),
    "expansion_ratio": ("1", 1.01, 80),
    "throat_area": ("m2", 1e-8, 1),
}


def resolve(value, overrides, sources, methods):
    normalized, pa = brief(value)
    if type(overrides) is not dict or set(overrides) - (set(RULES) | set(LOCKS)):
        raise InvalidInputError(
            "Only named guided profile overrides are allowed; no supplied results, paths, material allowables or worker commands."
        )
    parameters = []
    effective = {}
    for key, (number, unit, lower, upper, category, reason) in RULES.items():
        original = {"value": number, "unit": unit}
        chosen = overrides.get(key, original)
        scalar(chosen, unit, key, minimum=lower, maximum=upper)
        if (
            key in {"injector_holes", "nozzle_point_count"}
            and type(chosen["value"]) is not int
        ):
            raise InvalidInputError("Hole and contour point counts must be integers.")
        effective[key] = deepcopy(chosen)
        parameters.append(
            {
                "key": key,
                "quantity": deepcopy(chosen),
                "category": category,
                "basis": reason,
                "override": key in overrides,
                "original": original,
                "uncertainty": None,
                "source": "COSMOS explicitly provisional guided profile v1",
            }
        )
    for key, (unit, lower, upper) in LOCKS.items():
        if key in overrides:
            scalar(overrides[key], unit, key, minimum=lower, maximum=upper)
            effective[key] = deepcopy(overrides[key])
            parameters.append(
                {
                    "key": key,
                    "quantity": deepcopy(overrides[key]),
                    "category": "USER_INPUT",
                    "override": True,
                    "original": None,
                    "basis": "Explicit user lock; conflicts are reported, not silently tuned.",
                    "source": "User",
                    "uncertainty": None,
                }
            )
    parameters.append(
        {
            "key": "ambient_pressure",
            "quantity": {"value": pa, "unit": "Pa"},
            "category": "USER_INPUT"
            if normalized["environment"]["kind"] == "CUSTOM"
            else "CORRELATION_RULE",
            "basis": "Declared environment, not measured weather.",
            "source": "Standard sea-level convention / explicit vacuum or custom boundary",
            "uncertainty": None,
        }
    )
    result = {
        "schema": "cosmos.guided-resolution.v1",
        "profile_id": PROFILE_ID,
        "profile_version": 1,
        "brief": normalized,
        "overrides": deepcopy(overrides),
        "parameters": parameters,
        "effective": effective,
        "ambient_pressure_pa": pa,
        "property_package": deepcopy(sources),
        "method_sources": dict(methods),
        "selection": {
            "objective": "MAX_IDEAL_ISP_AT_DECLARED_AMBIENT",
            "of_min": 1.5,
            "of_max": 4.5,
            "coarse_step": 0.1,
            "refinement_step": 0.01,
            "vacuum_expansion_ratio": 20.0,
            "vacuum_basis": "Provisional finite Ae/At cap for a vacuum concept; infinite ideal expansion is not a finite design.",
            "thrust_relative_tolerance": 0.0002,
        },
        "limitations": [
            "Ideal infinite-area CEA equilibrium performance, not delivered hardware performance.",
            "Cold injector reference properties only at their exact retained T/P state; heated fuel is not substituted.",
            "Cooling architecture/material candidates require matched-state data; no hot allowables or selected seals are supplied.",
            "Regulated-feed budget does not establish full operating-point, pressurant or thermal closure.",
            "CAD generation and R08 remain ON_HOLD; existing matched models may be opened without a build.",
        ],
        "physical_validation": "NOT_PERFORMED",
        "intended_use": "PRELIMINARY_COMPUTATIONAL_DESIGN",
    }
    return {**result, "review_hash": digest(result)}
