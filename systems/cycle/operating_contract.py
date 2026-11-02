"""Strict explicit-unit contract for the selected downstream operating solver."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.feed.characteristics import RESISTANCE_UNIT, SPEED_HEAD_UNIT, SPEED_UNIT
from physics.si import (
    UNIT_DYNAMIC_VISCOSITY,
    UNIT_HTC,
    UNIT_SPECIFIC_ENERGY,
    UNIT_SPECIFIC_HEAT,
    UNIT_THERMAL_CONDUCTIVITY,
)
from systems.cycle.pressure_fed import _keys, _number, _source

SCHEMA = "cosmos.engine-operating-point-input.v1"
FEED_UNITS = {
    "density": "kg/m3", "cp": "J/kg/K", "viscosity": "Pa*s", "conductivity": "W/m/K",
    "temperature": "K", "reference_temperature": "K", "reference_pressure": "Pa", "tank_pressure": "Pa",
    "min_temperature": "K", "max_temperature": "K", "vapour_pressure": "Pa", "core_resistance": "Pa*s2/kg2",
}
PUMP_UNITS = {"speed_coefficient": "Pa*s2/rad2", "flow_coefficient": "Pa*s2/kg2", "speed_min": "rad/s", "speed_max": "rad/s", "flow_min": "kg/s", "flow_max": "kg/s"}
CORE_UNKNOWNS = {"chamber_pressure": "Pa", "oxidizer_flow": "kg/s", "fuel_flow": "kg/s"}
GG_UNKNOWNS = {"shaft_speed": "rad/s", "gg_pressure": "Pa", "gg_oxidizer_flow": "kg/s", "gg_fuel_flow": "kg/s"}
GG_UNITS = {"throat_area": "m2", "exhaust_pressure": "Pa", "auxiliary_power": "W", "oxidizer_resistance": "Pa*s2/kg2", "fuel_resistance": "Pa*s2/kg2"}
TOLERANCE_UNITS = {"pressure": "Pa", "mass_flow": "kg/s", "power": "W", "momentum": "N", "specific_energy": "J/kg"}


def quantity(value: float, unit: str) -> Quantity:
    custom = {
        "J/kg/K": UNIT_SPECIFIC_HEAT, "J/kg": UNIT_SPECIFIC_ENERGY, "Pa*s": UNIT_DYNAMIC_VISCOSITY,
        "W/m/K": UNIT_THERMAL_CONDUCTIVITY, "W/m2/K": UNIT_HTC, "rad/s": SPEED_UNIT,
        "Pa*s2/kg2": RESISTANCE_UNIT, "Pa*s2/rad2": SPEED_HEAD_UNIT,
    }
    return Quantity(value, custom[unit] if unit in custom else SI.get(unit))


def scalar(value: Any, unit: str, name: str, *, zero: bool = False) -> float:
    _keys(value, {"value", "unit"}, name)
    if value["unit"] != unit:
        raise InvalidInputError(f"{name} requires explicit SI {unit}; no conversion/default.")
    v = _number(value["value"], name)
    if abs(v) > 1e100 or v < 0 or (v == 0 and not zero):
        raise InvalidInputError(f"{name} outside finite positive domain.")
    return v


def count(value: Any, name: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise InvalidInputError(f"{name} requires an integer1..{maximum}.")
    return value


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    _keys(spec, {"schema", "cycle_type", "regime", "feeds", "gas_generator", "cooling", "unknowns", "solver", "tolerances"}, "operating specification")
    if spec["schema"] != SCHEMA or spec["regime"] != "STEADY_FROZEN_NOZZLE_CEA_HP" or spec["cycle_type"] not in {"PRESSURE_FED", "GAS_GENERATOR"}:
        raise InvalidInputError("Only declared steady pressure-fed/GG CEA HP operating models are supported.")
    out: dict[str, Any] = {"cycle_type": spec["cycle_type"]}
    _keys(spec["feeds"], {"fuel", "oxidizer"}, "feeds")
    for name, source in spec["feeds"].items():
        _keys(source, {*FEED_UNITS, "source", "phase", "pump", "gg_resistance"}, name)
        _source(source["source"], name + " enthalpy/properties/characteristics applicability")
        if source["phase"] != "LIQUID":
            raise InvalidInputError("Only explicit single-phase LIQUID feeds are supported.")
        values: dict[str, Any] = {key: scalar(source[key], unit, name + "." + key, zero=key == "vapour_pressure") for key, unit in FEED_UNITS.items()}
        if not values["min_temperature"] <= values["temperature"] <= values["max_temperature"] or values["min_temperature"] >= values["max_temperature"] or values["tank_pressure"] <= values["vapour_pressure"]:
            raise InvalidInputError("Invalid liquid property/phase window.")
        values["source"] = source["source"]
        if spec["cycle_type"] == "GAS_GENERATOR":
            pump = source["pump"]
            _keys(pump, {*PUMP_UNITS, "efficiency", "source"}, name + " pump")
            _source(pump["source"], "pump characteristic source")
            p = {key: scalar(pump[key], unit, "pump." + key, zero=key == "flow_coefficient") for key, unit in PUMP_UNITS.items()}
            p["efficiency"] = _number(pump["efficiency"], "pump efficiency")
            if not 0 < p["efficiency"] <= 1 or p["speed_min"] >= p["speed_max"] or p["flow_min"] >= p["flow_max"]:
                raise InvalidInputError("Invalid pump efficiency/map window.")
            values["pump"] = p
            values["gg_resistance"] = scalar(source["gg_resistance"], "Pa*s2/kg2", name + " GG resistance")
        elif source["pump"] is not None or source["gg_resistance"] is not None:
            raise InvalidInputError("Pressure-fed pump/GG resistance must explicitly be null.")
        out[name] = values
    gg = spec["gas_generator"]
    if spec["cycle_type"] == "GAS_GENERATOR":
        # GG branch resistances live on the corresponding feeds, not a duplicate.
        units = {key: unit for key, unit in GG_UNITS.items() if not key.endswith("resistance")}
        _keys(gg, {*units, "shaft_efficiency", "turbine_efficiency", "source"}, "gas_generator")
        _source(gg["source"], "GG/turbine applicability")
        out["gg"] = {key: scalar(gg[key], unit, "GG." + key, zero=key == "auxiliary_power") for key, unit in units.items()}
        for key in ("shaft_efficiency", "turbine_efficiency"):
            value = _number(gg[key], key)
            if not 0 < value <= 1:
                raise InvalidInputError("Explicit GG efficiencies must be in(0,1].")
            out["gg"][key] = value
    elif gg is not None:
        raise InvalidInputError("Pressure-fed gas_generator must be null.")
    cooling = spec["cooling"]
    units = {"wall_initial_temperature": "K", "wall_temperature_tolerance": "K", "heat_tolerance": "W", "gas_min_temperature": "K", "gas_max_temperature": "K"}
    _keys(cooling, {*units, "mode", "max_iterations", "relaxation", "source"}, "cooling")
    if cooling["mode"] not in {"NONE_EXPLICIT", "FUEL_CORE_SERIES"}:
        raise InvalidInputError("Only full-core fuel series cooling or explicit no-cooling supported; no film/mass injection fallback.")
    _source(cooling["source"], "thermal/property applicability")
    out["cooling"] = {key: scalar(cooling[key], unit, key) for key, unit in units.items()}
    out["cooling"]["mode"] = cooling["mode"]
    out["cooling"]["max_iterations"] = count(cooling["max_iterations"], "thermal max_iterations", 160)
    relax = _number(cooling["relaxation"], "thermal relaxation")
    if not 0 < relax <= 1 or out["cooling"]["gas_min_temperature"] >= out["cooling"]["gas_max_temperature"]:
        raise InvalidInputError("Invalid thermal relaxation/gas window.")
    out["cooling"]["relaxation"] = relax
    unknown_units = {**CORE_UNKNOWNS, **(GG_UNKNOWNS if gg is not None else {})}
    _keys(spec["unknowns"], set(unknown_units), "solver unknowns")
    out["unknowns"] = {}
    for key, unit in unknown_units.items():
        source = spec["unknowns"][key]
        _keys(source, {"initial", "lower", "upper", "scale"}, key)
        values = {k: scalar(v, unit, key + "." + k) for k, v in source.items()}
        if not values["lower"] < values["initial"] < values["upper"]:
            raise InvalidInputError("Initial unknowns must lie strictly inside explicit bounds.")
        out["unknowns"][key] = values
    solver = spec["solver"]
    _keys(solver, {"difference_step", "residual_tolerance", "max_iterations", "max_evaluations", "max_seconds"}, "solver")
    out["solver"] = {
        "max_iterations": count(solver["max_iterations"], "max_iterations", 100),
        "max_evaluations": count(solver["max_evaluations"], "max_evaluations", 5000),
        "max_seconds": scalar(solver["max_seconds"], "s", "max_seconds"),
    }
    for key in ("difference_step", "residual_tolerance"):
        value = _number(solver[key], key)
        if not 0 < value < 1:
            raise InvalidInputError("Normalized step/residual tolerance must be in(0,1).")
        out["solver"][key] = value
    if out["solver"]["max_seconds"] > 60:
        raise InvalidInputError("Synchronous operating solve has an explicit60s evaluation budget.")
    _keys(spec["tolerances"], set(TOLERANCE_UNITS), "dimensional acceptance tolerances")
    out["tolerances"] = {key: scalar(spec["tolerances"][key], unit, key) for key, unit in TOLERANCE_UNITS.items()}
    return deepcopy(out)
