"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_compressible_flow
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Unit tests for PHYS-004 compressible flow.
"""

from __future__ import annotations

import math

import pytest

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI

from physics.compressible_flow.area_mach import area_ratio, mach_from_area_ratio
from physics.compressible_flow.choked_flow import choked_mass_flow, is_choked
from physics.compressible_flow.expansion_fan import prandtl_meyer
from physics.compressible_flow.fanno import evaluate_fanno
from physics.compressible_flow.isentropic import (
    mach_from_pressure_ratio,
    stagnation_density_ratio,
    stagnation_pressure_ratio,
    stagnation_temperature_ratio,
)
from physics.compressible_flow.moc_nozzle import generate_contour, invariants, mach_angle
from physics.compressible_flow.normal_shock import evaluate_normal_shock
from physics.compressible_flow.nozzle_1d import station_from_area_ratio
from physics.compressible_flow.oblique_shock import deflection_from_wave_angle, evaluate_oblique_shock
from physics.compressible_flow.rayleigh import evaluate_rayleigh
from physics.compressible_flow.thrust_relations import ideal_thrust_coefficient, thrust
from physics.exceptions import InsufficientDataError
from physics.quantities import kelvin, pascal, square_metre
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol


GAMMA = 1.4


def test_mach_zero_stagnation_ratios_are_unity() -> None:
    assert stagnation_temperature_ratio(0.0, GAMMA) == pytest.approx(1.0)
    assert stagnation_pressure_ratio(0.0, GAMMA) == pytest.approx(1.0)
    assert stagnation_density_ratio(0.0, GAMMA) == pytest.approx(1.0)


def test_mach_one_area_ratio_is_unity() -> None:
    assert area_ratio(1.0, GAMMA) == pytest.approx(1.0, abs=1.0e-12)


def test_area_ratio_always_at_least_one() -> None:
    for mach in (0.3, 0.8, 1.0, 1.5, 3.0, 5.0):
        assert area_ratio(mach, GAMMA) >= 1.0 - 1.0e-12


def test_area_mach_inverse_round_trip() -> None:
    for mach, branch in ((0.5, "subsonic"), (2.0, "supersonic"), (4.0, "supersonic")):
        ar = area_ratio(mach, GAMMA)
        recovered = mach_from_area_ratio(ar, GAMMA, branch=branch)
        assert recovered == pytest.approx(mach, rel=1.0e-8)


def test_mach_zero_area_ratio_rejected() -> None:
    with pytest.raises(InvalidInputError):
        area_ratio(0.0, GAMMA)


def test_area_ratio_below_one_rejected() -> None:
    with pytest.raises(InvalidInputError):
        mach_from_area_ratio(0.9, GAMMA)


def test_gamma_one_rejected() -> None:
    with pytest.raises(InvalidInputError):
        stagnation_pressure_ratio(2.0, 1.0)


def test_normal_shock_mach_two_anderson() -> None:
    shock = evaluate_normal_shock(2.0, GAMMA)
    assert shock.mach_downstream == pytest.approx(0.57735, rel=1.0e-4)
    assert shock.pressure_ratio == pytest.approx(4.5, rel=1.0e-4)
    assert shock.density_ratio == pytest.approx(2.66667, rel=1.0e-4)
    assert shock.stagnation_pressure_ratio < 1.0


def test_normal_shock_approaches_identity_near_sonic() -> None:
    shock = evaluate_normal_shock(1.0001, GAMMA)
    assert shock.pressure_ratio == pytest.approx(1.0, rel=1.0e-3)
    assert shock.mach_downstream == pytest.approx(1.0, rel=1.0e-3)


def test_subsonic_normal_shock_rejected() -> None:
    with pytest.raises(InvalidInputError):
        evaluate_normal_shock(0.8, GAMMA)


def test_oblique_zero_deflection_is_mach_angle() -> None:
    state = evaluate_oblique_shock(2.5, 0.0, GAMMA)
    assert state.wave_angle_rad == pytest.approx(mach_angle(2.5), rel=1.0e-8)


def test_oblique_shock_pressure_rises() -> None:
    state = evaluate_oblique_shock(3.0, math.radians(20.0), GAMMA)
    assert state.pressure_ratio > 1.0
    assert state.mach_downstream < 3.0


def test_prandtl_meyer_zero_at_sonic() -> None:
    assert prandtl_meyer(1.0, GAMMA) == pytest.approx(0.0)


def test_prandtl_meyer_increases_with_mach() -> None:
    assert prandtl_meyer(3.0, GAMMA) > prandtl_meyer(2.0, GAMMA)


def test_fanno_and_rayleigh_sonic_identities() -> None:
    fanno = evaluate_fanno(1.0, GAMMA)
    rayleigh = evaluate_rayleigh(1.0, GAMMA)
    assert fanno.temperature_ratio == pytest.approx(1.0)
    assert fanno.friction_length_parameter == pytest.approx(0.0, abs=1.0e-12)
    assert rayleigh.temperature_ratio == pytest.approx(1.0)
    assert rayleigh.pressure_ratio == pytest.approx(1.0)
    assert rayleigh.stagnation_temperature_ratio == pytest.approx(1.0)


def test_choked_when_back_pressure_below_sonic() -> None:
    assert is_choked(0.5, GAMMA) is True
    assert is_choked(0.99, GAMMA) is False


def test_choked_mass_flow_positive() -> None:
    mdot = choked_mass_flow(
        pascal(1.0e6),
        kelvin(300.0),
        square_metre(0.01),
        GAMMA,
        molar_mass_from_kg_per_kmol(28.9647),
    )
    assert mdot.to_si() > 0.0


def test_nozzle_throat_station() -> None:
    station = station_from_area_ratio(
        1.0,
        pascal(1.0e6),
        kelvin(3000.0),
        GAMMA,
        molar_mass_from_kg_per_kmol(22.0),
        branch="supersonic",
    )
    assert station.mach == pytest.approx(1.0)
    assert station.pressure.to_si() < 1.0e6


def test_invalid_pressure_ratio() -> None:
    with pytest.raises(InvalidInputError):
        mach_from_pressure_ratio(1.2, GAMMA)


def test_thrust_adapted_nozzle() -> None:
    force = thrust(
        Quantity(1.0, SI.get("kg/s")),
        Quantity(2000.0, SI.get("m/s")),
        pascal(101325.0),
        pascal(101325.0),
        square_metre(0.1),
    )
    assert force.to_si() == pytest.approx(2000.0)


def test_ideal_cf_positive() -> None:
    cf = ideal_thrust_coefficient(GAMMA, 0.1, 0.1, 8.0)
    assert cf > 0.0


def test_moc_invariants_and_no_contour() -> None:
    inv = invariants(2.0, 0.1, GAMMA)
    assert inv.c_plus == pytest.approx(0.1 + inv.prandtl_meyer_rad)
    with pytest.raises(InsufficientDataError):
        generate_contour()


def test_deflection_from_mach_angle_is_zero() -> None:
    theta = deflection_from_wave_angle(2.0, mach_angle(2.0), GAMMA)
    assert theta == pytest.approx(0.0, abs=1.0e-12)
