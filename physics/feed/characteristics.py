"""Explicit SI liquid characteristic fits and incompressible enthalpy model."""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import DENSITY, MASS_FLOW_RATE, PRESSURE, TEMPERATURE, TIME
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import Unit
from physics.exceptions import OutOfRangeError
from physics.quantities import as_si
from physics.si import SPECIFIC_HEAT

RESISTANCE_UNIT = Unit("Pa*s2/kg2", "pressure per squared mass flow", PRESSURE / MASS_FLOW_RATE**2)
SPEED_HEAD_UNIT = Unit("Pa*s2/rad2", "pressure per squared angular speed", PRESSURE * TIME**2)
SPEED_UNIT = Unit("rad/s", "radians per second", TIME**-1)


def pressure_loss(flow: Quantity, resistance: Quantity) -> float:
    mass = as_si(flow, MASS_FLOW_RATE, "mass flow")
    k = as_si(resistance, RESISTANCE_UNIT.dimension, "resistance")
    if not all(math.isfinite(v) and v >= 0 for v in (mass, k)):
        raise InvalidInputError("Require nonnegative finite flow and resistance.")
    result = k * mass * mass
    if not math.isfinite(result):
        raise InvalidInputError("Resistance pressure loss overflow.")
    return result


@dataclass(frozen=True)
class PumpState:
    discharge_pressure_pa: float
    specific_work_j_kg: float
    power_w: float
    temperature_rise_k: float


def pump_state(
    *, pressure: Quantity, density: Quantity, cp: Quantity, flow: Quantity,
    speed: Quantity, speed_coefficient: Quantity, flow_coefficient: Quantity,
    efficiency: float,
) -> PumpState:
    p = as_si(pressure, PRESSURE, "pump inlet pressure")
    rho = as_si(density, DENSITY, "density")
    c = as_si(cp, SPECIFIC_HEAT, "liquid Cp")
    mass = as_si(flow, MASS_FLOW_RATE, "pump flow")
    omega = as_si(speed, SPEED_UNIT.dimension, "shaft speed")
    a = as_si(speed_coefficient, SPEED_HEAD_UNIT.dimension, "speed coefficient")
    b = as_si(flow_coefficient, RESISTANCE_UNIT.dimension, "flow coefficient")
    if not all(math.isfinite(v) and v > 0 for v in (p, rho, c, mass, omega, a)) or not math.isfinite(b) or b < 0 or type(efficiency) not in {float, int} or not 0 < efficiency <= 1:
        raise InvalidInputError("Invalid liquid pump characteristic inputs.")
    dp = a * omega**2 - b * mass**2
    if not math.isfinite(dp) or dp <= 0:
        raise OutOfRangeError("Supplied pump fit gives nonpositive pressure rise.")
    work = dp / (rho * efficiency)
    return PumpState(p + dp, work, work * mass, dp * (1 / efficiency - 1) / (rho * c))


def liquid_enthalpy_increment(
    *, temperature: Quantity, reference_temperature: Quantity,
    pressure: Quantity, reference_pressure: Quantity, density: Quantity, cp: Quantity,
) -> float:
    t = as_si(temperature, TEMPERATURE, "liquid temperature")
    tr = as_si(reference_temperature, TEMPERATURE, "reference temperature")
    p = as_si(pressure, PRESSURE, "liquid pressure")
    pr = as_si(reference_pressure, PRESSURE, "reference pressure")
    rho = as_si(density, DENSITY, "liquid density")
    c = as_si(cp, SPECIFIC_HEAT, "liquid Cp")
    if not all(math.isfinite(v) and v > 0 for v in (t, tr, p, pr, rho, c)):
        raise InvalidInputError("Finite positive liquid/reference state required.")
    return c * (t - tr) + (p - pr) / rho
