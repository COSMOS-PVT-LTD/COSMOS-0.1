"""
COSMOS Rocket Propulsion Platform

Module: physics.si
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Derived SI dimensions and units consumed by physics models.

Description:
    Constructs derived dimensions and units from Core ``Dimension`` and
    ``Unit``. Does not define a parallel unit system.
"""

from __future__ import annotations

from core.dimension import (
    AMOUNT,
    AREA,
    DIMENSIONLESS,
    ENERGY,
    FORCE,
    LENGTH,
    MASS,
    POWER,
    PRESSURE,
    TEMPERATURE,
    TIME,
    Dimension,
)
from core.unit import SI, Unit

__all__ = (
    "SPECIFIC_ENERGY",
    "SPECIFIC_HEAT",
    "MOLAR_MASS",
    "SPECIFIC_GAS_CONSTANT",
    "DYNAMIC_VISCOSITY",
    "KINEMATIC_VISCOSITY",
    "THERMAL_CONDUCTIVITY",
    "HEAT_TRANSFER_COEFFICIENT",
    "HEAT_FLUX",
    "SURFACE_TENSION",
    "STRESS",
    "STRAIN",
    "THERMAL_EXPANSION",
    "ANGULAR_WAVE_NUMBER",
    "UNIT_SPECIFIC_ENERGY",
    "UNIT_SPECIFIC_HEAT",
    "UNIT_MOLAR_MASS",
    "UNIT_MOLAR_ENERGY",
    "UNIT_MOLAR_ENTROPY",
    "UNIT_DYNAMIC_VISCOSITY",
    "UNIT_KINEMATIC_VISCOSITY",
    "UNIT_THERMAL_CONDUCTIVITY",
    "UNIT_HTC",
    "UNIT_HEAT_FLUX",
    "UNIT_SURFACE_TENSION",
    "UNIT_STRESS",
    "UNIT_STRAIN",
    "UNIT_ALPHA",
    "UNIT_PASCAL_SECOND",
)


SPECIFIC_ENERGY: Dimension = ENERGY / MASS
SPECIFIC_HEAT: Dimension = ENERGY / (MASS * TEMPERATURE)
MOLAR_MASS: Dimension = MASS / AMOUNT
SPECIFIC_GAS_CONSTANT: Dimension = ENERGY / (MASS * TEMPERATURE)
DYNAMIC_VISCOSITY: Dimension = MASS / (LENGTH * TIME)
KINEMATIC_VISCOSITY: Dimension = AREA / TIME
THERMAL_CONDUCTIVITY: Dimension = POWER / (LENGTH * TEMPERATURE)
HEAT_TRANSFER_COEFFICIENT: Dimension = POWER / (AREA * TEMPERATURE)
HEAT_FLUX: Dimension = POWER / AREA
SURFACE_TENSION: Dimension = FORCE / LENGTH
STRESS: Dimension = PRESSURE
STRAIN: Dimension = DIMENSIONLESS
THERMAL_EXPANSION: Dimension = DIMENSIONLESS / TEMPERATURE
ANGULAR_WAVE_NUMBER: Dimension = DIMENSIONLESS

UNIT_SPECIFIC_ENERGY = Unit("J/kg", "joule per kilogram", SPECIFIC_ENERGY)
UNIT_SPECIFIC_HEAT = Unit(
    "J/(kg K)",
    "joule per kilogram kelvin",
    SPECIFIC_HEAT,
)
UNIT_MOLAR_MASS = Unit("kg/mol", "kilogram per mole", MOLAR_MASS)
UNIT_MOLAR_ENERGY = Unit("J/mol", "joule per mole", ENERGY / AMOUNT)
UNIT_MOLAR_ENTROPY = Unit(
    "J/(mol K)",
    "joule per mole kelvin",
    ENERGY / (AMOUNT * TEMPERATURE),
)
UNIT_DYNAMIC_VISCOSITY = Unit("Pa s", "pascal second", DYNAMIC_VISCOSITY)
UNIT_PASCAL_SECOND = UNIT_DYNAMIC_VISCOSITY
UNIT_KINEMATIC_VISCOSITY = Unit(
    "m2/s",
    "square metre per second",
    KINEMATIC_VISCOSITY,
)
UNIT_THERMAL_CONDUCTIVITY = Unit(
    "W/(m K)",
    "watt per metre kelvin",
    THERMAL_CONDUCTIVITY,
)
UNIT_HTC = Unit(
    "W/(m2 K)",
    "watt per square metre kelvin",
    HEAT_TRANSFER_COEFFICIENT,
)
UNIT_HEAT_FLUX = Unit("W/m2", "watt per square metre", HEAT_FLUX)
UNIT_SURFACE_TENSION = Unit("N/m", "newton per metre", SURFACE_TENSION)
UNIT_STRESS = SI.get("Pa")
UNIT_STRAIN = SI.get("1")
UNIT_ALPHA = Unit("1/K", "per kelvin", THERMAL_EXPANSION)
