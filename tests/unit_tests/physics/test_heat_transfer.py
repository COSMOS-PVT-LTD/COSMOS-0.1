"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.physics.test_heat_transfer
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Unit tests for PHYS-005 heat transfer.
"""

from __future__ import annotations

import pytest

from core.quantity import Quantity
from core.unit import SI

from physics.exceptions import InsufficientDataError, OutOfRangeError
from physics.heat_transfer.bartz import bartz_heat_transfer_coefficient, sigma_correction
from physics.heat_transfer.conduction import plane_wall_heat_rate
from physics.heat_transfer.convection import newtons_law
from physics.heat_transfer.film_cooling import effectiveness
from physics.heat_transfer.heat_flux import convective_heat_flux
from physics.heat_transfer.radiation import net_heat_rate
from physics.heat_transfer.recovery_temperature import adiabatic_wall_temperature, recovery_factor
from physics.heat_transfer.thermal_resistance import conduction_resistance, convection_resistance, series_resistance
from physics.heat_transfer.transient_conduction import biot_number, lumped_temperature
from physics.quantities import kelvin, metre, pascal, square_metre
from physics.si import UNIT_DYNAMIC_VISCOSITY, UNIT_HTC, UNIT_SPECIFIC_HEAT, UNIT_THERMAL_CONDUCTIVITY
from physics.validity import ValidityStatus


def test_conduction_zero_when_isothermal() -> None:
    q = plane_wall_heat_rate(
        Quantity(16.0, UNIT_THERMAL_CONDUCTIVITY),
        square_metre(1.0),
        metre(0.01),
        kelvin(400.0),
        kelvin(400.0),
    )
    assert q.to_si() == pytest.approx(0.0)


def test_convection_and_radiation_signs() -> None:
    q_conv = newtons_law(Quantity(10.0, UNIT_HTC), square_metre(1.0), kelvin(400.0), kelvin(300.0))
    q_rad = net_heat_rate(0.8, square_metre(1.0), kelvin(400.0), kelvin(300.0))
    assert q_conv.to_si() > 0.0
    assert q_rad.to_si() > 0.0
    assert net_heat_rate(0.8, square_metre(1.0), kelvin(300.0), kelvin(300.0)).to_si() == pytest.approx(0.0)


def test_series_resistance_sum() -> None:
    r1 = conduction_resistance(metre(0.01), Quantity(16.0, UNIT_THERMAL_CONDUCTIVITY), square_metre(1.0))
    r2 = convection_resistance(Quantity(100.0, UNIT_HTC), square_metre(1.0))
    total = series_resistance((r1, r2))
    assert total.to_si() == pytest.approx(r1.to_si() + r2.to_si())


def test_recovery_mach_zero() -> None:
    taw = adiabatic_wall_temperature(kelvin(300.0), 0.0, 1.4, 0.7)
    assert taw.to_si() == pytest.approx(300.0)
    assert recovery_factor(1.0, regime="turbulent") == pytest.approx(1.0)


def test_sigma_unity_when_matched_temperatures_and_mach_zero() -> None:
    sigma = sigma_correction(0.0, 1.4, kelvin(500.0), kelvin(500.0))
    assert sigma == pytest.approx(1.0)


def test_bartz_si_nusselt_form() -> None:
    result = bartz_heat_transfer_coefficient(
        metre(0.05),
        Quantity(8.0e-5, UNIT_DYNAMIC_VISCOSITY),
        Quantity(0.3, UNIT_THERMAL_CONDUCTIVITY),
        Quantity(2000.0, UNIT_SPECIFIC_HEAT),
        pascal(5.0e6),
        Quantity(1500.0, SI.get("m/s")),
        1.0,
        1.2,
        kelvin(800.0),
        kelvin(2500.0),
    )
    assert result.reynolds > 1.0e4
    assert result.validity is ValidityStatus.VALID
    assert result.heat_transfer_coefficient.to_si() > 0.0
    assert result.nusselt == pytest.approx(
        0.026 * result.reynolds**0.8 * result.prandtl**0.4
    )


def test_heat_flux_zero_when_recovery_equals_wall() -> None:
    q = convective_heat_flux(Quantity(1000.0, UNIT_HTC), kelvin(800.0), kelvin(800.0))
    assert q.to_si() == pytest.approx(0.0)


def test_lumped_rejects_large_biot() -> None:
    with pytest.raises(OutOfRangeError):
        lumped_temperature(
            Quantity(1000.0, UNIT_HTC),
            square_metre(1.0),
            Quantity(0.001, SI.get("m3")),
            Quantity(8000.0, SI.get("kg/m3")),
            Quantity(500.0, UNIT_SPECIFIC_HEAT),
            Quantity(1.0, SI.get("s")),
            kelvin(400.0),
            kelvin(300.0),
            metre(0.01),
            Quantity(15.0, UNIT_THERMAL_CONDUCTIVITY),
        )


def test_lumped_initial_condition() -> None:
    bi = biot_number(Quantity(10.0, UNIT_HTC), metre(0.001), Quantity(50.0, UNIT_THERMAL_CONDUCTIVITY))
    assert bi < 0.1
    t = lumped_temperature(
        Quantity(10.0, UNIT_HTC),
        square_metre(0.01),
        Quantity(1.0e-5, SI.get("m3")),
        Quantity(8000.0, SI.get("kg/m3")),
        Quantity(500.0, UNIT_SPECIFIC_HEAT),
        Quantity(0.0, SI.get("s")),
        kelvin(400.0),
        kelvin(300.0),
        metre(0.001),
        Quantity(50.0, UNIT_THERMAL_CONDUCTIVITY),
    )
    assert t.to_si() == pytest.approx(400.0)


def test_film_cooling_not_invented() -> None:
    with pytest.raises(InsufficientDataError):
        effectiveness()
