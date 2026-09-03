"""
COSMOS Rocket Propulsion Platform

Module: tests.benchmark_tests.test_anderson_bartz
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Reference benchmarks for isentropic/shock (Anderson) and Bartz SI form.

Description:
    These are analytical / literature-equation benchmarks, not experimental
    validation of a rocket engine.
"""

from __future__ import annotations

import pytest

from core.quantity import Quantity
from core.unit import SI

from physics.compressible_flow.area_mach import area_ratio
from physics.compressible_flow.isentropic import (
    stagnation_pressure_ratio,
    stagnation_temperature_ratio,
)
from physics.compressible_flow.normal_shock import evaluate_normal_shock
from physics.heat_transfer.bartz import bartz_heat_transfer_coefficient
from physics.quantities import kelvin, metre, pascal
from physics.si import UNIT_DYNAMIC_VISCOSITY, UNIT_SPECIFIC_HEAT, UNIT_THERMAL_CONDUCTIVITY
from physics.thermochemistry.nasa_polynomials import evaluate_nasa7
from physics.thermochemistry.species import get_species


def test_anderson_isentropic_mach_two() -> None:
    """Anderson-style isentropic table, gamma=1.4, M=2."""

    gamma = 1.4
    assert stagnation_temperature_ratio(2.0, gamma) == pytest.approx(1.8, rel=1.0e-12)
    assert stagnation_pressure_ratio(2.0, gamma) == pytest.approx(7.82445, rel=1.0e-4)
    assert area_ratio(2.0, gamma) == pytest.approx(1.68750, rel=1.0e-4)


def test_anderson_normal_shock_mach_two() -> None:
    shock = evaluate_normal_shock(2.0, 1.4)
    assert shock.mach_downstream == pytest.approx(0.57735, rel=1.0e-4)
    assert shock.pressure_ratio == pytest.approx(4.50, rel=1.0e-4)
    assert shock.temperature_ratio == pytest.approx(1.68750, rel=1.0e-4)
    assert shock.density_ratio == pytest.approx(2.66667, rel=1.0e-4)


def test_nasa7_oxygen_cp_300k() -> None:
    o2 = get_species("O2")
    result = evaluate_nasa7(o2.polynomial, kelvin(300.0))
    # NIST Cp(O2, 298.15 K) ≈ 29.38 J/(mol K); 300 K is nearby.
    assert result.cp_molar.to_si() == pytest.approx(29.4, rel=0.02)


def test_bartz_nusselt_origin_independent_reference() -> None:
    """
    Independent worked example (SI Nusselt origin + curvature factor).

    Inputs are fixed constants. Expected ``h`` is computed from the
    dimensionless relation before calling the implementation:

        Nu = 0.026 Re^0.8 Pr^0.4
        h = Nu k / D * sigma * (D/R)^0.1
    """

    diameter_m = 0.04
    radius_m = 0.5
    mu = 9.0e-5
    k = 0.35
    cp = 1800.0
    pc = 7.0e6
    cstar = 1600.0
    mach = 0.2
    gamma = 1.2
    tw = 700.0
    taw = 2800.0

    g_star = pc / cstar
    reynolds = g_star * diameter_m / mu
    prandtl = mu * cp / k
    nusselt = 0.026 * reynolds**0.8 * prandtl**0.4
    recovery = 1.0 + 0.5 * (gamma - 1.0) * mach * mach
    inner = 0.5 * (tw / taw) * recovery + 0.5
    sigma = 1.0 / (inner**0.68 * recovery**0.12)
    curvature = (diameter_m / radius_m) ** 0.1
    expected_h = nusselt * k / diameter_m * sigma * curvature

    result = bartz_heat_transfer_coefficient(
        metre(diameter_m),
        Quantity(mu, UNIT_DYNAMIC_VISCOSITY),
        Quantity(k, UNIT_THERMAL_CONDUCTIVITY),
        Quantity(cp, UNIT_SPECIFIC_HEAT),
        pascal(pc),
        Quantity(cstar, SI.get("m/s")),
        mach,
        gamma,
        kelvin(tw),
        kelvin(taw),
        curvature_radius=metre(radius_m),
    )
    assert result.curvature_factor == pytest.approx(curvature, rel=1.0e-12)
    assert result.heat_transfer_coefficient.to_si() == pytest.approx(expected_h, rel=1.0e-12)
