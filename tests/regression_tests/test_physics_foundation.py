"""
COSMOS Rocket Propulsion Platform

Module: tests.regression_tests.test_physics_foundation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Regression locks for scientifically verified physics results.
"""

from __future__ import annotations

import pytest

from physics.compressible_flow.area_mach import area_ratio
from physics.compressible_flow.isentropic import stagnation_pressure_ratio
from physics.compressible_flow.normal_shock import evaluate_normal_shock
from physics.quantities import kelvin, pascal
from physics.thermodynamics.ideal_gas import density, molar_mass_from_kg_per_kmol


def test_regression_isentropic_mach_two() -> None:
    assert stagnation_pressure_ratio(2.0, 1.4) == pytest.approx(7.824449066867263, rel=1.0e-12)
    assert area_ratio(2.0, 1.4) == pytest.approx(1.687500000, rel=1.0e-6)


def test_regression_normal_shock_mach_two() -> None:
    shock = evaluate_normal_shock(2.0, 1.4)
    assert shock.mach_downstream == pytest.approx(0.577350269, rel=1.0e-8)
    assert shock.pressure_ratio == pytest.approx(4.5, rel=1.0e-12)


def test_regression_air_density_stp() -> None:
    rho = density(
        pascal(101325.0),
        kelvin(273.15),
        molar_mass_from_kg_per_kmol(28.9647),
    )
    assert rho.to_si() == pytest.approx(1.292, rel=0.01)
