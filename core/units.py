"""
COSMOS Rocket Propulsion Platform

Module: core.units
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Convert engineering values between supported units and SI units.

Description:
    Provides deterministic scalar conversion functions for values entering or
    leaving COSMOS. Solvers shall use SI units internally and shall not call
    these functions to mix unit systems during engineering calculations.

Example: ``bar_to_pascals(20.0)`` returns ``2000000.0`` Pa.
"""

from __future__ import annotations

# COSMOS Core
from core.constants import ATMOSPHERE_TO_PASCAL
from core.constants import BAR_TO_PASCAL
from core.constants import CELSIUS_ZERO_IN_KELVIN
from core.constants import CENTIMETER_TO_METER
from core.constants import DEGREE_TO_RADIAN
from core.constants import FOOT_TO_METER
from core.constants import HOUR_TO_SECOND
from core.constants import INCH_TO_METER
from core.constants import KILOMETER_TO_METER
from core.constants import MILLIMETER_TO_METER
from core.constants import MINUTE_TO_SECOND
from core.constants import POUND_FORCE_TO_NEWTON
from core.constants import POUND_MASS_TO_KILOGRAM
from core.constants import PSI_TO_PASCAL
from core.constants import RADIAN_TO_DEGREE

__all__ = (
    "atmospheres_to_pascals",
    "bar_to_pascals",
    "celsius_to_kelvin",
    "centimeters_to_meters",
    "degrees_to_radians",
    "feet_to_meters",
    "hours_to_seconds",
    "inches_to_meters",
    "kelvin_to_celsius",
    "kilograms_to_pounds_mass",
    "kilometers_to_meters",
    "meters_to_centimeters",
    "meters_to_feet",
    "meters_to_inches",
    "meters_to_kilometers",
    "meters_to_millimeters",
    "millimeters_to_meters",
    "minutes_to_seconds",
    "newtons_to_pounds_force",
    "pascals_to_atmospheres",
    "pascals_to_bar",
    "pascals_to_psi",
    "pounds_force_to_newtons",
    "pounds_mass_to_kilograms",
    "psi_to_pascals",
    "radians_to_degrees",
    "seconds_to_hours",
    "seconds_to_minutes",
)


def millimeters_to_meters(value: float) -> float:
    """Convert length from millimeters to meters.

    Parameters
    ----------
    value : float
        Length [mm].
    Returns
    -------
    float
        Length [m].
    """
    return value * MILLIMETER_TO_METER


def meters_to_millimeters(value: float) -> float:
    """Convert length from meters to millimeters.

    Parameters
    ----------
    value : float
        Length [m].
    Returns
    -------
    float
        Length [mm].
    """
    return value / MILLIMETER_TO_METER


def centimeters_to_meters(value: float) -> float:
    """Convert length from centimeters to meters.

    Parameters
    ----------
    value : float
        Length [cm].
    Returns
    -------
    float
        Length [m].
    """
    return value * CENTIMETER_TO_METER


def meters_to_centimeters(value: float) -> float:
    """Convert length from meters to centimeters.

    Parameters
    ----------
    value : float
        Length [m].
    Returns
    -------
    float
        Length [cm].
    """
    return value / CENTIMETER_TO_METER


def kilometers_to_meters(value: float) -> float:
    """Convert length from kilometers to meters.

    Parameters
    ----------
    value : float
        Length [km].
    Returns
    -------
    float
        Length [m].
    """
    return value * KILOMETER_TO_METER


def meters_to_kilometers(value: float) -> float:
    """Convert length from meters to kilometers.

    Parameters
    ----------
    value : float
        Length [m].
    Returns
    -------
    float
        Length [km].
    """
    return value / KILOMETER_TO_METER


def inches_to_meters(value: float) -> float:
    """Convert length from international inches to meters.

    Parameters
    ----------
    value : float
        Length [in].
    Returns
    -------
    float
        Length [m].
    """
    return value * INCH_TO_METER


def meters_to_inches(value: float) -> float:
    """Convert length from meters to international inches.

    Parameters
    ----------
    value : float
        Length [m].
    Returns
    -------
    float
        Length [in].
    """
    return value / INCH_TO_METER


def feet_to_meters(value: float) -> float:
    """Convert length from international feet to meters.

    Parameters
    ----------
    value : float
        Length [ft].
    Returns
    -------
    float
        Length [m].
    """
    return value * FOOT_TO_METER


def meters_to_feet(value: float) -> float:
    """Convert length from meters to international feet.

    Parameters
    ----------
    value : float
        Length [m].
    Returns
    -------
    float
        Length [ft].
    """
    return value / FOOT_TO_METER


def pounds_mass_to_kilograms(value: float) -> float:
    """Convert mass from avoirdupois pounds to kilograms.

    Parameters
    ----------
    value : float
        Mass [lb].
    Returns
    -------
    float
        Mass [kg].
    """
    return value * POUND_MASS_TO_KILOGRAM


def kilograms_to_pounds_mass(value: float) -> float:
    """Convert mass from kilograms to avoirdupois pounds.

    Parameters
    ----------
    value : float
        Mass [kg].
    Returns
    -------
    float
        Mass [lb].
    """
    return value / POUND_MASS_TO_KILOGRAM


def pounds_force_to_newtons(value: float) -> float:
    """Convert force from pounds-force to newtons.

    Parameters
    ----------
    value : float
        Force [lbf].
    Returns
    -------
    float
        Force [N].
    """
    return value * POUND_FORCE_TO_NEWTON


def newtons_to_pounds_force(value: float) -> float:
    """Convert force from newtons to pounds-force.

    Parameters
    ----------
    value : float
        Force [N].
    Returns
    -------
    float
        Force [lbf].
    """
    return value / POUND_FORCE_TO_NEWTON


def psi_to_pascals(value: float) -> float:
    """Convert pressure from pounds per square inch to pascals.

    Parameters
    ----------
    value : float
        Pressure [psi].
    Returns
    -------
    float
        Pressure [Pa].
    """
    return value * PSI_TO_PASCAL


def pascals_to_psi(value: float) -> float:
    """Convert pressure from pascals to pounds per square inch.

    Parameters
    ----------
    value : float
        Pressure [Pa].
    Returns
    -------
    float
        Pressure [psi].
    """
    return value / PSI_TO_PASCAL


def bar_to_pascals(value: float) -> float:
    """Convert pressure from bar to pascals.

    Parameters
    ----------
    value : float
        Pressure [bar].
    Returns
    -------
    float
        Pressure [Pa].
    """
    return value * BAR_TO_PASCAL


def pascals_to_bar(value: float) -> float:
    """Convert pressure from pascals to bar.

    Parameters
    ----------
    value : float
        Pressure [Pa].
    Returns
    -------
    float
        Pressure [bar].
    """
    return value / BAR_TO_PASCAL


def atmospheres_to_pascals(value: float) -> float:
    """Convert pressure from standard atmospheres to pascals.

    Parameters
    ----------
    value : float
        Pressure [atm].
    Returns
    -------
    float
        Pressure [Pa].
    """
    return value * ATMOSPHERE_TO_PASCAL


def pascals_to_atmospheres(value: float) -> float:
    """Convert pressure from pascals to standard atmospheres.

    Parameters
    ----------
    value : float
        Pressure [Pa].
    Returns
    -------
    float
        Pressure [atm].
    """
    return value / ATMOSPHERE_TO_PASCAL


def celsius_to_kelvin(value: float) -> float:
    """Convert temperature from degrees Celsius to kelvin.

    Parameters
    ----------
    value : float
        Temperature [deg C].
    Returns
    -------
    float
        Temperature [K].

    """
    return value + CELSIUS_ZERO_IN_KELVIN


def kelvin_to_celsius(value: float) -> float:
    """Convert temperature from kelvin to degrees Celsius.

    Parameters
    ----------
    value : float
        Temperature [K].
    Returns
    -------
    float
        Temperature [deg C].

    """
    return value - CELSIUS_ZERO_IN_KELVIN


def minutes_to_seconds(value: float) -> float:
    """Convert time from minutes to seconds.

    Parameters
    ----------
    value : float
        Time [min].
    Returns
    -------
    float
        Time [s].
    """
    return value * MINUTE_TO_SECOND


def seconds_to_minutes(value: float) -> float:
    """Convert time from seconds to minutes.

    Parameters
    ----------
    value : float
        Time [s].
    Returns
    -------
    float
        Time [min].
    """
    return value / MINUTE_TO_SECOND


def hours_to_seconds(value: float) -> float:
    """Convert time from hours to seconds.

    Parameters
    ----------
    value : float
        Time [h].
    Returns
    -------
    float
        Time [s].
    """
    return value * HOUR_TO_SECOND


def seconds_to_hours(value: float) -> float:
    """Convert time from seconds to hours.

    Parameters
    ----------
    value : float
        Time [s].
    Returns
    -------
    float
        Time [h].
    """
    return value / HOUR_TO_SECOND


def degrees_to_radians(value: float) -> float:
    """Convert plane angle from degrees to radians.

    Parameters
    ----------
    value : float
        Plane angle [deg].
    Returns
    -------
    float
        Plane angle [rad].
    """
    return value * DEGREE_TO_RADIAN


def radians_to_degrees(value: float) -> float:
    """Convert plane angle from radians to degrees.

    Parameters
    ----------
    value : float
        Plane angle [rad].
    Returns
    -------
    float
        Plane angle [deg].
    """
    return value * RADIAN_TO_DEGREE
