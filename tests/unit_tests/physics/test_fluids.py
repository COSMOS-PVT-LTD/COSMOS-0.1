"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_fluids
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Unit tests for PHYS-002 fluid properties.
"""

from __future__ import annotations

import pytest

from physics.exceptions import OutOfRangeError
from physics.fluids.fluid_properties import evaluate_record
from physics.fluids.helium import GAS_GAMMA as HELIUM_GAMMA
from physics.fluids.helium import MOLAR_MASS as HELIUM_MOLAR_MASS
from physics.fluids.lox import NBP_DENSITY as LOX_DENSITY
from physics.fluids.lox import NBP_TEMPERATURE_K
from physics.fluids.prandtl import prandtl_number
from physics.fluids.reynolds import reynolds_number
from physics.fluids.sutherland import AIR_SUTHERLAND, evaluate_sutherland
from physics.fluids.water import DENSITY_300K, VISCOSITY_300K
from physics.quantities import (
    kelvin,
    kilogram_per_cubic_metre,
    metre,
    metre_per_second,
    pascal,
)
from physics.si import UNIT_DYNAMIC_VISCOSITY, UNIT_THERMAL_CONDUCTIVITY
from physics.thermodynamics.ideal_gas import density as ideal_density
from physics.validity import ValidityStatus


def test_sutherland_recovers_reference_viscosity() -> None:
    result = evaluate_sutherland(AIR_SUTHERLAND, kelvin(273.15))
    assert result.validity is ValidityStatus.VALID
    assert result.viscosity.to_si() == pytest.approx(AIR_SUTHERLAND.mu_ref_pa_s, rel=1.0e-12)


def test_sutherland_monotonic_in_temperature() -> None:
    low = evaluate_sutherland(AIR_SUTHERLAND, kelvin(280.0)).viscosity.to_si()
    high = evaluate_sutherland(AIR_SUTHERLAND, kelvin(400.0)).viscosity.to_si()
    assert high > low


def test_sutherland_out_of_range_rejected() -> None:
    with pytest.raises(OutOfRangeError):
        evaluate_sutherland(AIR_SUTHERLAND, kelvin(50.0))


def test_sutherland_extrapolation_flag() -> None:
    result = evaluate_sutherland(
        AIR_SUTHERLAND,
        kelvin(50.0),
        allow_extrapolation=True,
    )
    assert result.validity is ValidityStatus.EXTRAPOLATED


def test_lox_nbp_density_valid_at_source_temperature() -> None:
    evaluation = evaluate_record(LOX_DENSITY, kelvin(NBP_TEMPERATURE_K), pascal(101325.0))
    assert evaluation.validity is ValidityStatus.VALID
    assert evaluation.require_valid().to_si() == pytest.approx(1141.0)


def test_lox_density_out_of_range_at_room_temperature() -> None:
    evaluation = evaluate_record(LOX_DENSITY, kelvin(300.0), pascal(101325.0))
    assert evaluation.validity is ValidityStatus.OUT_OF_RANGE
    with pytest.raises(OutOfRangeError):
        evaluation.require_valid()
    with pytest.raises(OutOfRangeError):
        _ = evaluation.quantity
    assert evaluation.stored_quantity.to_si() == pytest.approx(1141.0)


def test_water_300k_density() -> None:
    evaluation = evaluate_record(DENSITY_300K, kelvin(300.0), pascal(101325.0))
    assert evaluation.require_valid().to_si() == pytest.approx(997.0)


def test_reynolds_and_prandtl_dimensionless() -> None:
    mu = evaluate_record(VISCOSITY_300K, kelvin(300.0), pascal(101325.0)).require_valid()
    re = reynolds_number(
        kilogram_per_cubic_metre(997.0),
        metre_per_second(1.0),
        metre(0.01),
        mu,
    )
    assert re == pytest.approx(997.0 * 1.0 * 0.01 / mu.to_si())
    from core.quantity import Quantity

    pr = prandtl_number(
        mu,
        Quantity(4179.0, __import__("physics.si", fromlist=["UNIT_SPECIFIC_HEAT"]).UNIT_SPECIFIC_HEAT),
        Quantity(0.613, UNIT_THERMAL_CONDUCTIVITY),
    )
    assert pr == pytest.approx(5.83, rel=0.02)


def test_helium_monatomic_gamma() -> None:
    assert HELIUM_GAMMA == pytest.approx(5.0 / 3.0)
    rho = ideal_density(pascal(101325.0), kelvin(273.15), HELIUM_MOLAR_MASS)
    assert rho.to_si() == pytest.approx(0.1785, rel=0.02)


def test_negative_reynolds_velocity_rejected() -> None:
    with pytest.raises(Exception):
        reynolds_number(
            kilogram_per_cubic_metre(1.0),
            metre_per_second(-1.0),
            metre(1.0),
            __import__("physics.quantities", fromlist=["quantity"]).quantity(
                1.0e-5, UNIT_DYNAMIC_VISCOSITY
            ),
        )
