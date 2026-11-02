from dataclasses import replace

import pytest

from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.heat_transfer.temperature_wall import (
    ConductivityCurve,
    temperature_dependent_wall,
)
from physics.si import UNIT_HTC


def curve(values=(100.,100.,100.)):
    return ConductivityCurve("SYNTHETIC","Manufactured analytic fixture NOT alloy data",(100.,500.,1000.),values,
        "Synthetic constant/piecewise-linear conductivity, NOT hardware evidence","1"*64)


def balance(**updates):
    data={"gas_temperature":Quantity(900,SI.get("K")),"coolant_temperature":Quantity(200,SI.get("K")),
        "gas_coefficient":Quantity(100,UNIT_HTC),"coolant_coefficient":Quantity(500,UNIT_HTC),
        "gas_area":Quantity(.01,SI.get("m2")),"coolant_area":Quantity(.02,SI.get("m2")),"conduction_area":Quantity(.01,SI.get("m2")),
        "thickness":Quantity(.01,SI.get("m")),"conductivity":curve(),"heat_tolerance":Quantity(1e-7,SI.get("W")),"max_iterations":100}
    return temperature_dependent_wall(**(data|updates))


def test_constant_k_independent_series_resistance_and_three_energy_balances():
    result=balance();expected=700/(1/1+.01/(100*.01)+1/10)
    assert result.heat_w==pytest.approx(expected,abs=1e-7)
    assert result.hot_wall_temperature_k==pytest.approx(900-expected)
    assert result.cold_wall_temperature_k==pytest.approx(200+expected/10)
    assert abs(result.conduction_residual_w)<1e-7
    assert abs(result.gas_residual_w)<1e-10 and abs(result.coolant_residual_w)<1e-10


def test_linear_k_exact_integral_across_knots_and_nonlinear_wall_balance():
    material=curve((60.,100.,150.)) # k=50+.1T
    assert material.integral(200,900)==pytest.approx(50*700+.05*(900**2-200**2))
    result=balance(conductivity=material);th,tc=result.hot_wall_temperature_k,result.cold_wall_temperature_k
    independent=50*(th-tc)+.05*(th*th-tc*tc)
    assert result.heat_w==pytest.approx(independent,abs=1e-7)


def test_zero_heat_and_area_scaling():
    assert balance(gas_temperature=Quantity(200,SI.get("K"))).heat_w==0
    a=balance();b=balance(gas_area=Quantity(.02,SI.get("m2")),coolant_area=Quantity(.04,SI.get("m2")),conduction_area=Quantity(.02,SI.get("m2")))
    assert b.heat_w==pytest.approx(2*a.heat_w,abs=1e-7)
    assert b.hot_wall_temperature_k==pytest.approx(a.hot_wall_temperature_k)


def test_no_silent_material_window_or_cold_gas_fallback():
    with pytest.raises(OutOfRangeError):balance(conductivity=curve((.001,.001,.001)),gas_temperature=Quantity(3000,SI.get("K")))
    with pytest.raises(OutOfRangeError):balance(coolant_temperature=Quantity(950,SI.get("K")))
    with pytest.raises(DimensionError):balance(thickness=Quantity(1,SI.get("Pa")))


@pytest.mark.parametrize("updates",[{"temperatures_k":(300.,)},{"condition":""},{"source_sha256":"bad"},
    {"conductivities_w_m_k":(100.,-1.,100.)},{"temperatures_k":[100.,500.,1000.]}])
def test_source_condition_positive_bounded_immutable_curve_required(updates):
    with pytest.raises(InvalidInputError):replace(curve(),**updates)
