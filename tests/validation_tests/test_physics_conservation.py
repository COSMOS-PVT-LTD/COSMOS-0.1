"""
COSMOS Rocket Propulsion Platform

Module: tests.validation_tests.test_physics_conservation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Conservation and limiting-case validation for physics models.
"""

from __future__ import annotations

import pytest

from physics.compressible_flow.normal_shock import evaluate_normal_shock
from physics.quantities import kelvin, pascal
from physics.thermochemistry.mixtures import elemental_moles, from_mole_fractions
from physics.thermodynamics.ideal_gas import (
    density,
    molar_mass_from_kg_per_kmol,
    specific_enthalpy,
    specific_internal_energy,
    specific_gas_constant,
)


def test_mass_conservation_ideal_gas_state() -> None:
    m = molar_mass_from_kg_per_kmol(28.0)
    rho1 = density(pascal(2.0e5), kelvin(300.0), m)
    rho2 = density(pascal(1.0e5), kelvin(300.0), m)
    assert rho1.to_si() / rho2.to_si() == pytest.approx(2.0)


def test_energy_identity_h_equals_u_plus_rt() -> None:
    m = molar_mass_from_kg_per_kmol(28.0)
    t = kelvin(400.0)
    h = specific_enthalpy(t, 1.4, m)
    u = specific_internal_energy(t, 1.4, m)
    r = specific_gas_constant(m)
    assert h.to_si() == pytest.approx(u.to_si() + r.to_si() * 400.0)


def test_normal_shock_mass_momentum_energy_ratios() -> None:
    """Rankine–Hugoniot identities implied by the closed-form ratios."""

    shock = evaluate_normal_shock(3.0, 1.4)
    # Continuity: ρ2/ρ1 = (γ+1) M1^2 / ((γ-1) M1^2 + 2) already in the state.
    # Energy-consistent temperature ratio: T2/T1 = (p2/p1)/(ρ2/ρ1)
    assert shock.temperature_ratio == pytest.approx(
        shock.pressure_ratio / shock.density_ratio, rel=1.0e-12
    )
    assert shock.mach_downstream < 1.0


def test_elemental_conservation_through_mass_mole_convert() -> None:
    original = from_mole_fractions({"H2": 0.4, "O2": 0.6})
    counts = elemental_moles(original, 2.0)
    assert counts["H"] == pytest.approx(1.6)
    assert counts["O"] == pytest.approx(2.4)
