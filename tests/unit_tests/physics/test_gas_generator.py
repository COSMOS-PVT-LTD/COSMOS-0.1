"""Independent predeclared affine GG fixtures; synthetic, not hardware data."""

from dataclasses import replace

import pytest

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.feed.gas_generator import LiquidPump, Turbine, solve_power_balance
from physics.si import UNIT_SPECIFIC_HEAT


def q(value, unit):
    return Quantity(value, SI.get(unit))


def case(**edits):
    pump = LiquidPump(q(1000, "kg/m3"), q(1e6, "Pa"), q(2e6, "Pa"), 0.5)
    turbine = Turbine(
        q(1000, "K"),
        q(4e5, "Pa"),
        q(1e5, "Pa"),
        Quantity(1000, UNIT_SPECIFIC_HEAT),
        2,
        0.8,
        0.9,
    )
    return dict(
        oxidizer_base_flow=q(2, "kg/s"),
        fuel_base_flow=q(1, "kg/s"),
        oxidizer_pump=pump,
        fuel_pump=pump,
        turbine=turbine,
        gg_mixture_ratio=1,
        auxiliary_power=q(0, "W"),
        maximum_gg_flow=q(1, "kg/s"),
        **edits,
    )


def test_independent_affine_reference_includes_pumping_gg_itself():
    result = solve_power_balance(**case())
    assert result.gg_mass_flow_kg_s == pytest.approx(3 / 179, rel=1e-13)
    assert result.turbine_outlet_total_temperature_k == pytest.approx(600, abs=1e-10)
    assert result.feedback_denominator_j_kg == pytest.approx(358000)
    assert result.delivered_shaft_power_w == pytest.approx(6000 + 2000 * (3 / 179))
    assert result.oxidizer_pump_flow_kg_s == pytest.approx(2 + 3 / 358)
    assert result.gg_fuel_flow_kg_s == pytest.approx(3 / 358)
    assert abs(result.shaft_residual_w) < 1e-9
    assert abs(result.turbine_energy_residual_w) < 1e-9
    assert result.iterations == 0 and result.termination == "DIRECT_AFFINE"


def test_independent_auxiliary_film_and_separate_gg_ratio():
    args = case()
    args["auxiliary_power"] = q(100, "W")
    assert solve_power_balance(**args).gg_mass_flow_kg_s == pytest.approx(6100 / 358000)
    args = case()
    args["fuel_base_flow"] = q(1.1, "kg/s")
    assert solve_power_balance(**args).gg_mass_flow_kg_s == pytest.approx(6200 / 358000)
    args["gg_mixture_ratio"] = 2
    out = solve_power_balance(**args)
    assert out.gg_oxidizer_flow_kg_s / out.gg_fuel_flow_kg_s == pytest.approx(2)


def test_infeasible_feedback_and_explicit_limit_refuse():
    args = case()
    args["turbine"] = replace(args["turbine"], shaft_efficiency=0.001)
    with pytest.raises(InvalidInputError, match="INFEASIBLE_POWER_FEEDBACK"):
        solve_power_balance(**args)
    args = case()
    args["maximum_gg_flow"] = q(0.01, "kg/s")
    with pytest.raises(InvalidInputError, match="INFEASIBLE_GG_FLOW"):
        solve_power_balance(**args)


@pytest.mark.parametrize("field", ["efficiency", "shaft_efficiency"])
@pytest.mark.parametrize("value", [0, -1, 1.01, True, float("nan"), float("inf")])
def test_bad_efficiencies_refused(field, value):
    args = case()
    args["turbine"] = replace(args["turbine"], **{field: value})
    with pytest.raises(InvalidInputError):
        solve_power_balance(**args)


@pytest.mark.parametrize("value", [0, -1, True, float("inf")])
def test_invalid_gg_ratio_refused(value):
    args = case()
    args["gg_mixture_ratio"] = value
    with pytest.raises(InvalidInputError):
        solve_power_balance(**args)


def test_no_expansion_wrong_dimension_and_boolean_pump_refused():
    args = case()
    args["turbine"] = replace(args["turbine"], outlet_total_pressure=q(4e5, "Pa"))
    with pytest.raises(InvalidInputError):
        solve_power_balance(**args)
    args = case()
    args["fuel_pump"] = replace(args["fuel_pump"], efficiency=True)
    with pytest.raises(InvalidInputError):
        solve_power_balance(**args)
