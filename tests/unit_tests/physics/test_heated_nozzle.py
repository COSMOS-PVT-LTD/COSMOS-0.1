"""Independent conservation and isentropic-limit grid verification, not experiments."""
import math
from itertools import pairwise

import pytest

from core.exceptions import InvalidInputError
from physics.compressible_flow.heated_nozzle import nonadiabatic_nozzle
from physics.feed.characteristics import (
    liquid_enthalpy_increment,
    pressure_loss,
    pump_state,
)
from physics.heat_transfer.pressure_cooling import pressure_coupled_cooling
from physics.heat_transfer.regenerative import CoolingInputs, GasWallStation
from systems.cycle.operating_contract import quantity as q


def nozzle(count, heat=0):
    areas = tuple(q(.001 * (1 + 3 * (i / count)**2), "m2") for i in range(count + 1))
    return nonadiabatic_nozzle(q(1e6, "Pa"), q(1000, "K"), q(1400, "J/kg/K"), q(400, "J/kg/K"), areas, tuple(q(heat / count, "W") for _ in range(count)))


def test_sonic_independent_and_energy_momentum():
    result = nozzle(64, 10000)
    # gamma=1.4, T*=1000/1.2, P*=1MPa/1.2^3.5.
    t = 1000 / 1.2
    p = 1e6 / 1.2**3.5
    expected = p * .001 * math.sqrt(1.4 * 400 * t) / (400 * t)
    assert result.mass_flow_kg_s == pytest.approx(expected)
    assert result.stations[-1].total_enthalpy_j_kg == pytest.approx(1400e3 - 10000 / expected)
    assert abs(result.energy_residual_w) < 1e-8
    assert max(abs(v) for v in result.momentum_residuals_n) < 1e-9


def test_zero_heat_refines_toward_independent_area_mach_solution():
    # Solve the independent analytic area-Mach equation with a local test-only
    # bisection; do not compare the discretization against itself.
    lo, hi = 1., 5.
    for _ in range(100):
        m = (lo + hi) / 2
        area_ratio = ((2 / 2.4) * (1 + .2 * m*m))**3 / m
        if area_ratio < 4:
            lo = m
        else:
            hi = m
    expected = (lo + hi) / 2
    errors = [abs(nozzle(n).stations[-1].mach - expected) for n in (32, 64, 128, 256)]
    assert all(b < a for a, b in pairwise(errors))
    assert errors[-1] < .002


def test_heat_extraction_is_not_an_adiabatic_nozzle_result():
    cold, cooled = nozzle(128), nozzle(128, 1e5)
    assert cooled.stations[-1].total_enthalpy_j_kg < cold.stations[-1].total_enthalpy_j_kg
    assert cooled.stations[-1].pressure_pa != cold.stations[-1].pressure_pa


def test_invalid_order_or_heat_is_not_clipped():
    with pytest.raises(InvalidInputError):
        nonadiabatic_nozzle(q(1e6,"Pa"), q(1000,"K"), q(1400,"J/kg/K"), q(400,"J/kg/K"), (q(.1,"m2"),q(.1,"m2")), (q(0,"W"),))


def test_independent_liquid_characteristic_and_pump_enthalpy():
    assert pressure_loss(q(2,"kg/s"), q(10,"Pa*s2/kg2")) == 40
    result = pump_state(pressure=q(1e5,"Pa"), density=q(1000,"kg/m3"), cp=q(1000,"J/kg/K"), flow=q(2,"kg/s"), speed=q(10,"rad/s"), speed_coefficient=q(1000,"Pa*s2/rad2"), flow_coefficient=q(1000,"Pa*s2/kg2"), efficiency=.5)
    assert result.discharge_pressure_pa == 196000
    assert result.power_w == 384
    assert result.temperature_rise_k == .096
    assert liquid_enthalpy_increment(temperature=q(301,"K"),reference_temperature=q(300,"K"),pressure=q(2e5,"Pa"),reference_pressure=q(1e5,"Pa"),density=q(1000,"kg/m3"),cp=q(1000,"J/kg/K")) == 1100


def test_coolant_pressure_enthalpy_exact_constant_segment():
    inputs = CoolingInputs(q(1,"kg/s"),q(300,"K"),q(8e6,"Pa"),q(800,"kg/m3"),q(.0005,"Pa*s"),q(.6,"W/m/K"),q(2500,"J/kg/K"),q(.001,"m"),q(.001,"m"),q(.0005,"m"),60,q(.0005,"m"),q(300,"W/m/K"),q(200,"K"),q(1500,"K"),q(2000,"K"),q(1e5,"Pa"),"exit_to_throat")
    stations = tuple(GasWallStation(q(x,"m"),q(.02,"m"),q(1000,"W/m2/K"),q(1200,"K")) for x in (0.,.2))
    result = pressure_coupled_cooling(stations,inputs)
    reynolds, pr, dh = 1/(60*.001**2)*.001/.0005, .0005*2500/.6, .001
    velocity = 1/(800*60*.001**2)
    dp = .3164*reynolds**-.25*.2/dh*800*velocity**2/2
    hc = .023*reynolds**.8*pr**.4*.6/dh
    hot,cold = 2*math.pi*.02*.2,60*.001*.2
    ua = hot/(1/1000+.0005/300+hot/(cold*hc))
    equilibrium = 1200+dp/(800*ua)
    expected = equilibrium-(equilibrium-300)*math.exp(-ua/2500)
    assert result.outlet_temperature_k == pytest.approx(expected)
    assert result.total_pressure_loss_pa == pytest.approx(dp)
    assert result.total_heat_w == pytest.approx(2500*(expected-300)-dp/800)
    assert abs(result.energy_residual_w) < 1e-8
