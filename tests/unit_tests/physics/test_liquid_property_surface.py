from dataclasses import replace

import pytest

from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import OutOfRangeError
from physics.fluids.liquid_table import LiquidState, LiquidTable
from physics.si import UNIT_SPECIFIC_ENERGY


def analytic(t,p):
    pressure=p/1e5
    return LiquidState(600-t+pressure,2000*(t-100)+30*pressure+2*(t-100)*pressure,
                       2000+2*pressure,1e-4*(1+.001*(t-100))*(1+.01*pressure),.2+.001*(t-100)+.0001*pressure)


def table():
    ts=(110.,120.,130.);ps=(5e5,6e5,8e5)
    return LiquidTable("SYNTHETIC_liquid",ts,ps,tuple(tuple(analytic(t,p) for p in ps) for t in ts),
                       135.,"Synthetic analytic interpolation fixture, NOT NIST or hardware data","synthetic common reference",("1"*64,))


@pytest.mark.parametrize("t,p",[(110.,5e5),(130.,8e5),(117.,5.5e5),(125.,7e5),(120.,6e5)])
def test_bilinear_reference_and_enthalpy_inverse(t,p):
    source=table();actual=source.evaluate(Quantity(t,SI.get("K")),Quantity(p,SI.get("Pa")))
    expected=analytic(t,p)
    for key in ("density_kg_m3","enthalpy_j_kg","cp_j_kg_k","viscosity_pa_s","conductivity_w_m_k"):
        assert getattr(actual,key)==pytest.approx(getattr(expected,key),rel=1e-13)
    assert source.temperature_for_enthalpy(Quantity(actual.enthalpy_j_kg,UNIT_SPECIFIC_ENERGY),Quantity(p,SI.get("Pa")))==pytest.approx(t,abs=1e-12)


@pytest.mark.parametrize("t,p",[(109.,6e5),(131.,6e5),(120.,4e5),(120.,9e5)])
def test_no_heating_pressure_or_phase_domain_fallback(t,p):
    with pytest.raises(OutOfRangeError):table().evaluate(Quantity(t,SI.get("K")),Quantity(p,SI.get("Pa")))


def test_enthalpy_domain_and_core_dimensions():
    with pytest.raises(OutOfRangeError):table().temperature_for_enthalpy(Quantity(1e8,UNIT_SPECIFIC_ENERGY),Quantity(6e5,SI.get("Pa")))
    with pytest.raises(DimensionError):table().evaluate(Quantity(120,SI.get("m")),Quantity(6e5,SI.get("Pa")))


@pytest.mark.parametrize("changes",[{"temperatures_k":(110.,)},{"pressures_pa":(8e5,5e5)},
    {"lowest_saturation_temperature_k":130.},{"source":""},{"enthalpy_reference":""},{"raw_sha256":("bad",)},
    {"states":((LiquidState(1,1,1,1,1),),)},{"temperatures_k":[110.,120.,130.]}])
def test_reject_one_point_windows_invalid_grids_missing_source_and_mutable_data(changes):
    with pytest.raises(InvalidInputError):replace(table(),**changes)


def test_nonmonotone_enthalpy_cannot_be_inverted():
    source=table();rows=tuple(tuple(replace(s,enthalpy_j_kg=1.) for s in row) for row in source.states)
    with pytest.raises(InvalidInputError):replace(source,states=rows)
