"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_thermochemistry
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Unit tests for PHYS-003 thermochemistry.
"""

from __future__ import annotations

import pytest

from core.constants import UNIVERSAL_GAS_CONSTANT

from physics.exceptions import InsufficientDataError, InvalidCompositionError
from physics.quantities import kelvin, pascal
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from physics.thermochemistry.mixtures import elemental_moles, from_mass_fractions, from_mole_fractions
from physics.thermochemistry.nasa_polynomials import evaluate_nasa7
from physics.thermochemistry.reactions import Reaction, check_elemental_balance
from physics.thermochemistry.species import get_species, list_species
from physics.thermochemistry.transport_properties import wilke_mixture_viscosity
from physics.validity import ValidityStatus


def test_species_registry_contains_propulsion_set() -> None:
    names = set(list_species())
    for item in ("N2", "O2", "H2", "H2O", "CO2", "CH4", "HE"):
        assert item in names


def test_molar_mass_matches_elements() -> None:
    n2 = get_species("N2")
    assert n2.molar_mass.to_si() == pytest.approx(0.0280134, rel=1.0e-3)


def test_nasa7_n2_cp_near_300k() -> None:
    n2 = get_species("N2")
    result = evaluate_nasa7(n2.polynomial, kelvin(300.0))
    assert result.validity is ValidityStatus.VALID
    cp = result.cp_molar.to_si()
    assert cp == pytest.approx(29.1, rel=0.02)


def test_nasa7_out_of_range() -> None:
    n2 = get_species("N2")
    with pytest.raises(Exception):
        evaluate_nasa7(n2.polynomial, kelvin(50.0))


def test_argon_cp_over_r_is_2_5() -> None:
    ar = get_species("AR")
    result = evaluate_nasa7(ar.polynomial, kelvin(300.0))
    assert result.cp_over_r == pytest.approx(2.5)
    assert result.cp_molar.to_si() == pytest.approx(2.5 * UNIVERSAL_GAS_CONSTANT)


def test_mole_fractions_must_sum_to_one() -> None:
    with pytest.raises(InvalidCompositionError):
        from_mole_fractions({"N2": 0.5, "O2": 0.4})


def test_optional_normalization_is_reported() -> None:
    mixture = from_mole_fractions({"N2": 2.0, "O2": 2.0}, normalize=True)
    assert mixture.was_normalized is True
    assert mixture.mole_fractions["N2"] == pytest.approx(0.5)


def test_negative_fraction_rejected() -> None:
    with pytest.raises(InvalidCompositionError):
        from_mole_fractions({"N2": 1.2, "O2": -0.2})


def test_mass_mole_round_trip() -> None:
    original = from_mole_fractions({"N2": 0.79, "O2": 0.21})
    via_mass = from_mass_fractions(original.mass_fractions)
    assert via_mass.mole_fractions["N2"] == pytest.approx(0.79, rel=1.0e-12)
    assert via_mass.mean_molar_mass.to_si() == pytest.approx(
        original.mean_molar_mass.to_si(), rel=1.0e-12
    )


def test_elemental_moles_airlike() -> None:
    mixture = from_mole_fractions({"N2": 0.79, "O2": 0.21})
    counts = elemental_moles(mixture, 1.0)
    assert counts["N"] == pytest.approx(1.58)
    assert counts["O"] == pytest.approx(0.42)


def test_reaction_elemental_balance() -> None:
    ok = Reaction("h2_ox", {"H2": 2.0, "O2": 1.0}, {"H2O": 2.0})
    check_elemental_balance(ok)
    bad = Reaction("unbalanced", {"H2": 1.0}, {"H2O": 1.0})
    with pytest.raises(InvalidCompositionError):
        check_elemental_balance(bad)


def test_cea_without_engine_is_insufficient() -> None:
    request = CeaRequest("CH4", "O2", 3.5, pascal(1.0e6))
    with pytest.raises(InsufficientDataError):
        run_thermochemistry(request)


def test_wilke_single_species_identity() -> None:
    mixture = from_mole_fractions({"N2": 1.0})
    from physics.quantities import quantity
    from physics.si import UNIT_DYNAMIC_VISCOSITY

    mu = quantity(1.8e-5, UNIT_DYNAMIC_VISCOSITY)
    mix = wilke_mixture_viscosity(mixture, {"N2": mu})
    assert mix.to_si() == pytest.approx(1.8e-5)
