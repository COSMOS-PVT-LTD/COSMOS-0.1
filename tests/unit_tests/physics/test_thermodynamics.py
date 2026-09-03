"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_thermodynamics
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Unit tests for PHYS-001 thermodynamics.
"""

from __future__ import annotations

import pytest

from core.constants import G0, UNIVERSAL_GAS_CONSTANT
from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI

from physics.exceptions import InsufficientDataError
from physics.quantities import kelvin, metre, metre_per_second, pascal
from physics.si import UNIT_MOLAR_MASS, UNIT_SPECIFIC_ENERGY, UNIT_SPECIFIC_HEAT
from physics.thermodynamics.enthalpy import specific_from_internal_energy
from physics.thermodynamics.equations_of_state import compressibility_factor
from physics.thermodynamics.exergy import ideal_gas_flow_exergy
from physics.thermodynamics.first_law import closed_system_delta_u, steady_flow_energy_residual
from physics.thermodynamics.ideal_gas import (
    cp_from_gamma,
    cv_from_gamma,
    density,
    evaluate_state,
    gamma_from_specific_heats,
    molar_mass_from_kg_per_kmol,
    pressure,
    specific_enthalpy,
    specific_entropy_change,
    specific_gas_constant,
    specific_internal_energy,
    speed_of_sound,
)
from physics.thermodynamics.phase_equilibrium import integrated_pressure_ratio, slope
from physics.thermodynamics.real_gas import peng_robinson
from physics.thermodynamics.second_law import entropy_production_closed, is_possible_process


def _air_molar_mass() -> Quantity:
    return molar_mass_from_kg_per_kmol(28.9647)


def test_ideal_gas_eos_identity() -> None:
    m = _air_molar_mass()
    t = kelvin(300.0)
    p = pascal(101325.0)
    rho = density(p, t, m)
    p_back = pressure(rho, t, m)
    assert p_back.approx_equal(p, rel_tol=1.0e-12)


def test_compressibility_is_one_for_ideal_gas() -> None:
    m = _air_molar_mass()
    t = kelvin(300.0)
    p = pascal(101325.0)
    rho = density(p, t, m)
    z = compressibility_factor(p, rho, t, specific_gas_constant(m))
    assert z == pytest.approx(1.0, rel=1.0e-12)


def test_cp_minus_cv_equals_r() -> None:
    m = _air_molar_mass()
    cp = cp_from_gamma(1.4, m)
    cv = cv_from_gamma(1.4, m)
    r = specific_gas_constant(m)
    assert (cp.to_si() - cv.to_si()) == pytest.approx(r.to_si(), rel=1.0e-12)
    assert gamma_from_specific_heats(cp, cv) == pytest.approx(1.4)


def test_speed_of_sound_dimensions_and_value() -> None:
    m = _air_molar_mass()
    a = speed_of_sound(kelvin(273.15), 1.4, m)
    assert a.dimension().is_compatible_with(SI.get("m/s").dimension)
    assert a.to_si() == pytest.approx(331.0, rel=0.01)


def test_isentropic_entropy_change_is_zero() -> None:
    m = _air_molar_mass()
    t1 = kelvin(300.0)
    p1 = pascal(101325.0)
    t2 = kelvin(400.0)
    p2_si = p1.to_si() * (400.0 / 300.0) ** (1.4 / 0.4)
    ds = specific_entropy_change(t1, t2, p1, pascal(p2_si), 1.4, m)
    assert ds.to_si() == pytest.approx(0.0, abs=1.0e-9)


def test_enthalpy_internal_energy_identity() -> None:
    m = _air_molar_mass()
    t = kelvin(350.0)
    h = specific_enthalpy(t, 1.4, m)
    u = specific_internal_energy(t, 1.4, m)
    r = specific_gas_constant(m)
    assert (h.to_si() - u.to_si()) == pytest.approx(r.to_si() * 350.0, rel=1.0e-12)


def test_enthalpy_from_u_plus_pv() -> None:
    m = _air_molar_mass()
    t = kelvin(300.0)
    p = pascal(1.0e5)
    rho = density(p, t, m)
    u = specific_internal_energy(t, 1.4, m)
    h = specific_from_internal_energy(u, p, rho)
    assert h.to_si() == pytest.approx(specific_enthalpy(t, 1.4, m).to_si(), rel=1.0e-12)


def test_first_law_adiabatic() -> None:
    du = closed_system_delta_u(Quantity(0.0, SI.get("J")), Quantity(10.0, SI.get("J")))
    assert du.to_si() == pytest.approx(-10.0)


def test_steady_flow_residual_zero_for_balanced_case() -> None:
    residual = steady_flow_energy_residual(
        Quantity(100.0, UNIT_SPECIFIC_ENERGY),
        metre_per_second(0.0),
        metre_per_second(10.0),
        metre(0.0),
        metre(0.0),
        Quantity(150.0, UNIT_SPECIFIC_ENERGY),
        Quantity(0.0, UNIT_SPECIFIC_ENERGY),
        Quantity(G0, SI.get("m/s2")),
    )
    assert residual == pytest.approx(0.0, abs=1.0e-12)


def test_second_law_reversible_zero_production() -> None:
    from core.unit import Unit
    from core.dimension import ENERGY, TEMPERATURE

    entropy_unit = Unit("J/K", "joule per kelvin", ENERGY / TEMPERATURE)
    ds = Quantity(1.0, entropy_unit)
    q = Quantity(300.0, SI.get("J"))
    sigma = entropy_production_closed(ds, q, kelvin(300.0))
    assert sigma.to_si() == pytest.approx(0.0, abs=1.0e-12)
    assert is_possible_process(sigma)


def test_gamma_equals_one_is_rejected() -> None:
    with pytest.raises(InvalidInputError):
        cp_from_gamma(1.0, _air_molar_mass())


def test_negative_temperature_rejected() -> None:
    with pytest.raises(InvalidInputError):
        density(pascal(1.0e5), kelvin(-1.0), _air_molar_mass())


def test_dimension_mismatch_rejected() -> None:
    with pytest.raises(DimensionError):
        density(kelvin(300.0), kelvin(300.0), _air_molar_mass())


def test_flow_exergy_zero_at_environment() -> None:
    m = _air_molar_mass()
    t0 = kelvin(298.15)
    p0 = pascal(101325.0)
    psi = ideal_gas_flow_exergy(t0, p0, t0, p0, 1.4, m)
    assert psi.to_si() == pytest.approx(0.0, abs=1.0e-9)


def test_peng_robinson_is_not_invented() -> None:
    with pytest.raises(InsufficientDataError):
        peng_robinson()


def test_clausius_clapeyron_round_trip() -> None:
    from core.dimension import MASS, VOLUME
    from core.unit import Unit

    ratio = integrated_pressure_ratio(
        kelvin(300.0),
        kelvin(310.0),
        Quantity(2.26e6, UNIT_SPECIFIC_ENERGY),
        Quantity(461.5, UNIT_SPECIFIC_HEAT),
    )
    assert ratio > 1.0
    specific_volume = Unit("m3/kg", "cubic metre per kilogram", VOLUME / MASS)
    dp_dt = slope(
        Quantity(2.26e6, UNIT_SPECIFIC_ENERGY),
        kelvin(373.15),
        Quantity(1.67, specific_volume),
    )
    assert dp_dt.to_si() > 0.0


def test_evaluate_state_validity() -> None:
    state = evaluate_state(pascal(1.0e6), kelvin(500.0), _air_molar_mass(), 1.4)
    assert state.gamma == 1.4
    assert state.density.to_si() > 0.0


def test_r_univ_used_not_hardcoded() -> None:
    m = Quantity(0.028, UNIT_MOLAR_MASS)
    r = specific_gas_constant(m)
    assert r.to_si() == pytest.approx(UNIVERSAL_GAS_CONSTANT / 0.028)
