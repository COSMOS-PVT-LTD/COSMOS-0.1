import math

import pytest

from core.exceptions import DimensionError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.feed.heated_liquid_segment import darcy_factor, heated_liquid_segment
from physics.fluids.liquid_table import LiquidState, LiquidTable
from physics.si import UNIT_SPECIFIC_ENERGY


def table():
    ts=(110.,120.,130.);ps=(5e5,6e5,8e5)
    return LiquidTable("SYNTHETIC",ts,ps,tuple(tuple(LiquidState(1000.,2000*(t-100)+p/1000,2000.,.001,.5) for p in ps) for t in ts),
        135.,"Synthetic incompressible analytic reference, NOT NIST or hardware evidence","h=Cp(T-100)+P/rho",("1"*64,))


def segment(**updates):
    q=lambda v,u:Quantity(v,SI.get(u))
    values={"table":table(),"mass_flow":q(.001,"kg/s"),"inlet_temperature":q(115.,"K"),"inlet_pressure":q(7e5,"Pa"),
        "outlet_pressure_min":q(5e5,"Pa"),"length":q(1.,"m"),"diameter":q(.01,"m"),"roughness":q(0.,"m"),
        "minor_loss":q(0.,"1"),"heat":q(0.,"W"),"pressure_tolerance":q(1e-5,"Pa"),
        "specific_energy_tolerance":Quantity(1e-7,UNIT_SPECIFIC_ENERGY),"max_iterations":100,
        "loss_source":"Manufactured straight circular test pipe; explicitly zero fitting loss, not engine hardware"}
    return heated_liquid_segment(**(values|updates))


def test_laminar_poiseuille_loss_and_adiabatic_enthalpy_invariance():
    result=segment();u=.001/(1000*math.pi*.01**2/4)
    expected=32*.001*1*u/.01**2
    assert result.friction_pressure_loss_pa==pytest.approx(expected,rel=1e-12)
    assert 7e5-result.outlet_pressure_pa==pytest.approx(expected,abs=1e-5)
    assert result.outlet_temperature_k==pytest.approx(115+expected/(1000*2000),abs=1e-10)
    assert result.acceleration_pressure_loss_pa==0 and abs(result.energy_residual_j_kg)<1e-7


def test_prescribed_heat_uses_enthalpy_not_frozen_inlet_properties():
    result=segment(heat=Quantity(10,SI.get("W")))
    expected=115+10/(.001*2000)+(7e5-result.outlet_pressure_pa)/(1000*2000)
    assert result.outlet_temperature_k==pytest.approx(expected,abs=1e-10)
    assert abs(result.momentum_residual_pa)<1e-5


def test_turbulent_factor_satisfies_independent_colebrook_equation():
    f=darcy_factor(1e5,.0001)
    assert 1/math.sqrt(f)+2*math.log10(.0001/3.7+2.51/(1e5*math.sqrt(f)))==pytest.approx(0,abs=1e-11)
    assert f==pytest.approx(.018513866077,rel=1e-9)


@pytest.mark.parametrize("re,roughness",[(3000,0),(0,0),(1e9,0),(1e5,.1),(True,0)])
def test_transition_or_friction_domain_is_not_guessed(re,roughness):
    with pytest.raises(OutOfRangeError):darcy_factor(re,roughness)


def test_cell_split_preserves_exact_constant_density_balances():
    whole=segment(heat=Quantity(10,SI.get("W")))
    first=segment(heat=Quantity(5,SI.get("W")),length=Quantity(.5,SI.get("m")))
    second=segment(heat=Quantity(5,SI.get("W")),length=Quantity(.5,SI.get("m")),
        inlet_temperature=Quantity(first.outlet_temperature_k,SI.get("K")),inlet_pressure=Quantity(first.outlet_pressure_pa,SI.get("Pa")))
    assert second.outlet_pressure_pa==pytest.approx(whole.outlet_pressure_pa,abs=2e-5)
    assert second.outlet_temperature_k==pytest.approx(whole.outlet_temperature_k,abs=1e-9)


def test_phase_energy_pressure_and_geometry_domains_fail_closed():
    with pytest.raises(OutOfRangeError):segment(heat=Quantity(100,SI.get("W")))
    with pytest.raises(OutOfRangeError):segment(diameter=Quantity(.0001,SI.get("m")))
    with pytest.raises(OutOfRangeError):segment(length=Quantity(.01,SI.get("m")))
    with pytest.raises(DimensionError):segment(heat=Quantity(1,SI.get("m")))
