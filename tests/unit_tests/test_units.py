"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.test_units
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Verify COSMOS unit conversion utilities.

Description:
    Tests known conversion values, inverse conversion pairs, temperature
    offsets, public exports, and public function type hints.
"""

from __future__ import annotations

# Standard Library
from collections.abc import Callable
from inspect import isfunction
from typing import get_type_hints

# Third Party
import pytest

# COSMOS Core
from core import units


@pytest.mark.parametrize(
    ("converter", "source_value", "expected_value"),
    (
        (units.millimeters_to_meters, 1_000.0, 1.0),
        (units.centimeters_to_meters, 100.0, 1.0),
        (units.kilometers_to_meters, 1.0, 1_000.0),
        (units.inches_to_meters, 1.0, 0.0254),
        (units.feet_to_meters, 1.0, 0.3048),
        (units.pounds_mass_to_kilograms, 1.0, 0.453_592_37),
        (units.pounds_force_to_newtons, 1.0, 4.448_221_615_260_5),
        (units.psi_to_pascals, 1.0, 6_894.757_293_168_361),
        (units.bar_to_pascals, 1.0, 100_000.0),
        (units.atmospheres_to_pascals, 1.0, 101_325.0),
        (units.minutes_to_seconds, 1.0, 60.0),
        (units.hours_to_seconds, 1.0, 3_600.0),
        (units.degrees_to_radians, 180.0, 3.141_592_653_589_793),
    ),
)
def test_known_conversions(
    converter: Callable[[float], float],
    source_value: float,
    expected_value: float,
) -> None:
    """Verify representative conversions against defined values."""
    assert converter(source_value) == pytest.approx(expected_value)


@pytest.mark.parametrize(
    ("to_si", "from_si"),
    (
        (units.millimeters_to_meters, units.meters_to_millimeters),
        (units.centimeters_to_meters, units.meters_to_centimeters),
        (units.kilometers_to_meters, units.meters_to_kilometers),
        (units.inches_to_meters, units.meters_to_inches),
        (units.feet_to_meters, units.meters_to_feet),
        (units.pounds_mass_to_kilograms, units.kilograms_to_pounds_mass),
        (units.pounds_force_to_newtons, units.newtons_to_pounds_force),
        (units.psi_to_pascals, units.pascals_to_psi),
        (units.bar_to_pascals, units.pascals_to_bar),
        (units.atmospheres_to_pascals, units.pascals_to_atmospheres),
        (units.minutes_to_seconds, units.seconds_to_minutes),
        (units.hours_to_seconds, units.seconds_to_hours),
        (units.degrees_to_radians, units.radians_to_degrees),
    ),
)
@pytest.mark.parametrize("value", (-125.5, 0.0, 4_200.25))
def test_inverse_conversion_pairs_round_trip(
    to_si: Callable[[float], float],
    from_si: Callable[[float], float],
    value: float,
) -> None:
    """Verify each multiplicative conversion pair is reversible."""
    assert from_si(to_si(value)) == pytest.approx(value)


@pytest.mark.parametrize(
    ("celsius", "kelvin"),
    (
        (-273.15, 0.0),
        (0.0, 273.15),
        (100.0, 373.15),
    ),
)
def test_temperature_conversions(celsius: float, kelvin: float) -> None:
    """Verify Celsius and kelvin offset conversions."""
    assert units.celsius_to_kelvin(celsius) == pytest.approx(kelvin)
    assert units.kelvin_to_celsius(kelvin) == pytest.approx(celsius)


def test_public_exports_are_unique_typed_functions() -> None:
    """Verify all exported conversion functions are fully typed."""
    assert len(units.__all__) == len(set(units.__all__))

    for name in units.__all__:
        converter = getattr(units, name)
        type_hints = get_type_hints(converter)

        assert isfunction(converter)
        assert type_hints == {"value": float, "return": float}
