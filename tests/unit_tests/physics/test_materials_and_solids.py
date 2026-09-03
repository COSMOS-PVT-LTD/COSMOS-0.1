"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_materials_and_solids
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Unit tests for PHYS-006 and PHYS-007.
"""

from __future__ import annotations

import math

import pytest

from core.quantity import Quantity
from core.unit import SI

from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.materials.catalog import OFHC_COPPER, STAINLESS_304, get_material
from physics.materials.creep_models import norton_rate
from physics.materials.elastic_properties import youngs_modulus
from physics.materials.failure_criteria import yield_ratio
from physics.quantities import kelvin, metre, newton, pascal, square_metre
from physics.solid_mechanics.buckling import euler_load
from physics.solid_mechanics.elasticity import shear_modulus, uniaxial_stress
from physics.solid_mechanics.pressure_vessels import cylinder, sphere
from physics.solid_mechanics.safety_factor import ratio
from physics.solid_mechanics.stress import normal_stress, principal_stress_2d, von_mises
from physics.solid_mechanics.thermal_stress import constrained_bar


def test_material_lookup() -> None:
    material = get_material("stainless_304")
    assert material.material_id == "stainless_304"


def test_room_temperature_not_universal() -> None:
    with pytest.raises(OutOfRangeError):
        youngs_modulus(STAINLESS_304, kelvin(900.0)).require_valid()


def test_copper_conductivity_at_300k() -> None:
    k = OFHC_COPPER.conductivity
    from physics.fluids.fluid_properties import evaluate_record

    value = evaluate_record(k, kelvin(300.0)).require_valid()
    assert value.to_si() == pytest.approx(401.0)


def test_creep_not_invented() -> None:
    with pytest.raises(InsufficientDataError):
        norton_rate()


def test_hooke_and_von_mises_uniaxial() -> None:
    stress = uniaxial_stress(pascal(200.0e9), 0.001)
    assert stress.to_si() == pytest.approx(2.0e8)
    vm = von_mises(2.0e8, 0.0, 0.0)
    assert vm.to_si() == pytest.approx(2.0e8)


def test_hydrostatic_von_mises_is_zero() -> None:
    assert von_mises(10.0e6, 10.0e6, 10.0e6).to_si() == pytest.approx(0.0)


def test_principal_stress_pure_shear() -> None:
    s1, s2 = principal_stress_2d(pascal(0.0), pascal(0.0), pascal(50.0e6))
    assert s1 == pytest.approx(50.0e6)
    assert s2 == pytest.approx(-50.0e6)


def test_thin_wall_cylinder_roark() -> None:
    result = cylinder(pascal(1.0e6), metre(0.1), metre(0.002))
    assert result.hoop.to_si() == pytest.approx(50.0e6)
    assert result.longitudinal.to_si() == pytest.approx(25.0e6)
    assert result.radius_to_thickness == pytest.approx(50.0)
    sph = sphere(pascal(1.0e6), metre(0.1), metre(0.002))
    assert sph.to_si() == pytest.approx(25.0e6)


def test_constrained_thermal_stress() -> None:
    from physics.si import UNIT_ALPHA

    sigma = constrained_bar(
        pascal(200.0e9),
        Quantity(12.0e-6, UNIT_ALPHA),
        Quantity(50.0, SI.get("K")),
    )
    assert sigma.to_si() == pytest.approx(200.0e9 * 12.0e-6 * 50.0)


def test_euler_pinned_column() -> None:
    from core.dimension import LENGTH
    from core.unit import Unit

    inertia_unit = Unit("m4", "metre to the fourth", LENGTH**4)
    load = euler_load(pascal(200.0e9), Quantity(1.0e-8, inertia_unit), metre(1.0), 1.0)
    expected = (math.pi**2) * 200.0e9 * 1.0e-8 / 1.0
    assert load.to_si() == pytest.approx(expected)


def test_normal_stress_and_safety_factor() -> None:
    sigma = normal_stress(newton(1000.0), square_metre(0.01))
    assert sigma.to_si() == pytest.approx(1.0e5)
    assert ratio(2.0e5, sigma.to_si()) == pytest.approx(2.0)


def test_yield_ratio_stainless() -> None:
    n = yield_ratio(pascal(107.5e6), STAINLESS_304, kelvin(300.0))
    assert n == pytest.approx(0.5)


def test_shear_modulus_identity() -> None:
    g = shear_modulus(pascal(200.0e9), 0.3)
    assert g.to_si() == pytest.approx(200.0e9 / (2.0 * 1.3))
