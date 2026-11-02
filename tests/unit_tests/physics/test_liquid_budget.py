import pytest

from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.heat_transfer.liquid_budget import liquid_heating_threshold
from physics.si import UNIT_SPECIFIC_ENERGY


def threshold(mdot=2., incoming=-1000., saturation=99000., duration=5.):
    return liquid_heating_threshold(mass_flow=Quantity(mdot,SI.get("kg/s")),
        inlet_enthalpy=Quantity(incoming,UNIT_SPECIFIC_ENERGY),
        saturated_liquid_enthalpy=Quantity(saturation,UNIT_SPECIFIC_ENERGY),
        duration=Quantity(duration,SI.get("s")))


def test_independent_steady_energy_balance_and_enthalpy_reference_invariance():
    result = threshold()
    assert result.specific_enthalpy_margin_j_kg == 100000.
    assert result.saturation_onset_heat_w == 200000.
    assert result.duration_heat_j == 1000000.
    assert threshold(incoming=99000.,saturation=199000.) == result
    assert threshold(mdot=4.).saturation_onset_heat_w == 2 * result.saturation_onset_heat_w


@pytest.mark.parametrize("kwargs", [{"mdot":0}, {"duration":0}, {"incoming":99000}, {"incoming":100000},
                                    {"incoming":float("nan")}, {"saturation":float("inf")}])
def test_absent_subcooled_margin_and_invalid_values_fail(kwargs):
    with pytest.raises(InvalidInputError):
        threshold(**kwargs)


def test_dimension_check_before_balance():
    with pytest.raises(DimensionError):
        liquid_heating_threshold(mass_flow=Quantity(1,SI.get("kg/s")), inlet_enthalpy=Quantity(1,SI.get("K")),
            saturated_liquid_enthalpy=Quantity(2,UNIT_SPECIFIC_ENERGY), duration=Quantity(5,SI.get("s")))
