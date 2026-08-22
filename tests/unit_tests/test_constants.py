"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.test_constants
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Verify the shared COSMOS constants.

Description:
    Tests physical values, mathematical relationships, unit conversions,
    exports, and constant type annotations.
"""

from __future__ import annotations

# Standard Library
from math import isclose
from typing import Final, get_origin, get_type_hints

# COSMOS Core
from core import constants


def test_standard_gravity_matches_defined_value() -> None:
    """Verify the exact standard acceleration due to gravity."""
    assert constants.G0 == 9.806_65


def test_exact_si_defining_constants() -> None:
    """Verify the SI-defining physical constants used by COSMOS."""
    assert constants.SPEED_OF_LIGHT == 299_792_458.0
    assert constants.PLANCK_CONSTANT == 6.626_070_15e-34
    assert constants.ELEMENTARY_CHARGE == 1.602_176_634e-19
    assert constants.BOLTZMANN_CONSTANT == 1.380_649e-23
    assert constants.AVOGADRO_CONSTANT == 6.022_140_76e23


def test_universal_gas_constant_is_derived_from_si_constants() -> None:
    """Verify the molar gas constant is derived without duplication."""
    expected = (
        constants.BOLTZMANN_CONSTANT * constants.AVOGADRO_CONSTANT
    )
    assert constants.UNIVERSAL_GAS_CONSTANT == expected
    assert isclose(
        constants.UNIVERSAL_GAS_CONSTANT,
        8.314_462_618_153_24,
        rel_tol=1.0e-15,
    )


def test_angular_conversions_are_reciprocal() -> None:
    """Verify degree and radian conversions are mutually consistent."""
    assert isclose(
        constants.DEGREE_TO_RADIAN * constants.RADIAN_TO_DEGREE,
        1.0,
        rel_tol=1.0e-15,
    )


def test_imperial_conversions_are_consistent() -> None:
    """Verify exact imperial-to-SI conversion relationships."""
    assert isclose(
        constants.FOOT_TO_METER,
        12.0 * constants.INCH_TO_METER,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert constants.POUND_FORCE_TO_NEWTON == (
        constants.POUND_MASS_TO_KILOGRAM * constants.G0
    )
    assert constants.PSI_TO_PASCAL == (
        constants.POUND_FORCE_TO_NEWTON / constants.INCH_TO_METER**2
    )


def test_standard_pressure_conversions() -> None:
    """Verify standard pressure conversion factors."""
    assert constants.BAR_TO_PASCAL == 100_000.0
    assert constants.ATMOSPHERE_TO_PASCAL == 101_325.0


def test_all_exports_are_unique_floats_annotated_as_final() -> None:
    """Verify every public constant has the required export and type."""
    assert len(constants.__all__) == len(set(constants.__all__))
    type_hints = get_type_hints(constants, include_extras=True)

    for name in constants.__all__:
        value = getattr(constants, name)
        annotation = type_hints[name]

        assert isinstance(value, float)
        assert get_origin(annotation) is Final
