"""
COSMOS Rocket Propulsion Platform

Module: core.constants
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Provide shared mathematical, physical, and unit constants.

Description:
    Defines the immutable-by-convention constants used throughout COSMOS.
    Physical constants follow the 2022 CODATA values published by NIST.
    Defined unit conversions follow the International System of Units (SI).

Examples
--------
Calculate weight at standard gravity:

>>> mass = 12.0
>>> weight = mass * G0
>>> weight
117.6798
"""

from __future__ import annotations

# Standard Library
from math import e, pi, sqrt, tau
from typing import Final

__all__ = (
    "ATMOSPHERE_TO_PASCAL",
    "AVOGADRO_CONSTANT",
    "BAR_TO_PASCAL",
    "BOLTZMANN_CONSTANT",
    "CELSIUS_ZERO_IN_KELVIN",
    "CENTIMETER_TO_METER",
    "DEGREE_TO_RADIAN",
    "ELEMENTARY_CHARGE",
    "EULER_NUMBER",
    "FOOT_TO_METER",
    "G0",
    "GRAVITATIONAL_CONSTANT",
    "INCH_TO_METER",
    "KILOMETER_TO_METER",
    "MILLIMETER_TO_METER",
    "MINUTE_TO_SECOND",
    "HOUR_TO_SECOND",
    "PI",
    "PLANCK_CONSTANT",
    "POUND_FORCE_TO_NEWTON",
    "POUND_MASS_TO_KILOGRAM",
    "PSI_TO_PASCAL",
    "RADIAN_TO_DEGREE",
    "SPEED_OF_LIGHT",
    "SQRT_TWO",
    "STANDARD_ATMOSPHERE",
    "STEFAN_BOLTZMANN_CONSTANT",
    "TAU",
    "UNIVERSAL_GAS_CONSTANT",
)


# Mathematical constants
PI: Final[float] = pi
"""Ratio of a circle's circumference to its diameter [-]."""

TAU: Final[float] = tau
"""Ratio of a circle's circumference to its radius [-]."""

EULER_NUMBER: Final[float] = e
"""Base of the natural logarithm [-]."""

SQRT_TWO: Final[float] = sqrt(2.0)
"""Principal square root of two [-]."""


# Exact SI-defining constants
SPEED_OF_LIGHT: Final[float] = 299_792_458.0
"""Speed of light in vacuum [m/s], exact."""

PLANCK_CONSTANT: Final[float] = 6.626_070_15e-34
"""Planck constant [J s], exact."""

ELEMENTARY_CHARGE: Final[float] = 1.602_176_634e-19
"""Elementary electric charge [C], exact."""

BOLTZMANN_CONSTANT: Final[float] = 1.380_649e-23
"""Boltzmann constant [J/K], exact."""

AVOGADRO_CONSTANT: Final[float] = 6.022_140_76e23
"""Avogadro constant [mol^-1], exact."""

UNIVERSAL_GAS_CONSTANT: Final[float] = (
    BOLTZMANN_CONSTANT * AVOGADRO_CONSTANT
)
"""Universal molar gas constant [J/(mol K)], exact by definition."""


# Physical and standard-condition constants
GRAVITATIONAL_CONSTANT: Final[float] = 6.674_30e-11
"""Newtonian constant of gravitation [m^3/(kg s^2)]."""

STEFAN_BOLTZMANN_CONSTANT: Final[float] = 5.670_374_419e-8
"""Stefan-Boltzmann constant [W/(m^2 K^4)]."""

G0: Final[float] = 9.806_65
"""Standard acceleration due to gravity [m/s^2], exact."""

STANDARD_ATMOSPHERE: Final[float] = 101_325.0
"""Standard atmosphere [Pa], exact."""

CELSIUS_ZERO_IN_KELVIN: Final[float] = 273.15
"""Thermodynamic temperature of zero degrees Celsius [K], exact."""


# Exact scale and time conversions
MILLIMETER_TO_METER: Final[float] = 1.0e-3
"""Meters per millimeter [m/mm], exact."""

CENTIMETER_TO_METER: Final[float] = 1.0e-2
"""Meters per centimeter [m/cm], exact."""

KILOMETER_TO_METER: Final[float] = 1.0e3
"""Meters per kilometer [m/km], exact."""

MINUTE_TO_SECOND: Final[float] = 60.0
"""Seconds per minute [s/min], exact."""

HOUR_TO_SECOND: Final[float] = 3_600.0
"""Seconds per hour [s/h], exact."""

DEGREE_TO_RADIAN: Final[float] = PI / 180.0
"""Radians per degree [rad/deg], exact relationship."""

RADIAN_TO_DEGREE: Final[float] = 180.0 / PI
"""Degrees per radian [deg/rad], exact relationship."""


# Exact non-SI input and display conversions
INCH_TO_METER: Final[float] = 0.0254
"""Meters per international inch [m/in], exact."""

FOOT_TO_METER: Final[float] = 0.3048
"""Meters per international foot [m/ft], exact."""

POUND_MASS_TO_KILOGRAM: Final[float] = 0.453_592_37
"""Kilograms per international avoirdupois pound [kg/lb], exact."""

POUND_FORCE_TO_NEWTON: Final[float] = (
    POUND_MASS_TO_KILOGRAM * G0
)
"""Newtons per pound-force [N/lbf], exact relationship."""

PSI_TO_PASCAL: Final[float] = POUND_FORCE_TO_NEWTON / INCH_TO_METER**2
"""Pascals per pound-force per square inch [Pa/psi]."""

BAR_TO_PASCAL: Final[float] = 100_000.0
"""Pascals per bar [Pa/bar], exact."""

ATMOSPHERE_TO_PASCAL: Final[float] = STANDARD_ATMOSPHERE
"""Pascals per standard atmosphere [Pa/atm], exact."""
