"""Independent hand-calculated SI budgets, not experimental rocket evidence."""

from dataclasses import replace

import pytest

from core.dimension import PRESSURE
from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI, Unit
from physics.feed.pressure_fed import (
    PRESSURE_FED,
    PressureLoss,
    liquid_feed_budget,
    steady_mass_residual,
)


def q(value, unit):
    return Quantity(value, SI.get(unit))


def inputs(**edits):
    return {
        "mass_flow": q(2, "kg/s"),
        "density": q(1000, "kg/m3"),
        "source_pressure": q(182000, "Pa"),
        "required_sink_pressure": q(100000, "Pa"),
        "outlet_area": q(0.001, "m2"),
        "source_velocity": q(0, "m/s"),
        "elevation_rise": q(3, "m"),
        "gravitational_acceleration": q(10, "m/s2"),
        "losses": (
            PressureLoss("pipe", q(20000, "Pa")),
            PressureLoss("valve", q(30000, "Pa")),
        ),
        **edits,
    }


def test_independent_constant_reference():
    r = liquid_feed_budget(**inputs())
    for actual, expected in (
        (r.volumetric_flow_m3_s, 0.002),
        (r.outlet_velocity_m_s, 2),
        (r.kinetic_pressure_change_pa, 2000),
        (r.elevation_pressure_change_pa, 30000),
        (r.irreversible_loss_pa, 50000),
        (r.required_source_pressure_pa, 182000),
        (r.pressure_residual_pa, 0),
        (r.dissipated_mechanical_power_w, 100),
    ):
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-9)


@pytest.mark.parametrize("supply,residual", [(181000, -1000), (183000, 1000)])
def test_signed_pressure_residual_does_not_modify_flow(supply, residual):
    r = liquid_feed_budget(**inputs(source_pressure=q(supply, "Pa")))
    assert r.pressure_residual_pa == residual
    assert r.mass_flow_kg_s == 2
    assert r.required_source_pressure_pa == 182000


@pytest.mark.parametrize(
    "edits,expected",
    [
        ({"elevation_rise": q(-3, "m")}, 122000),
        ({"gravitational_acceleration": q(0, "m/s2")}, 152000),
        ({"source_velocity": q(2, "m/s")}, 180000),
        ({"outlet_area": q(0.0005, "m2")}, 188000),
        ({"source_velocity": q(4, "m/s")}, 174000),
    ],
)
def test_head_sign_gravity_and_area_independent_constants(edits, expected):
    assert liquid_feed_budget(**inputs(**edits)).required_source_pressure_pa == expected


def test_lossless_equal_velocity_horizontal_limit():
    r = liquid_feed_budget(
        **inputs(
            source_velocity=q(2, "m/s"),
            elevation_rise=q(0, "m"),
            losses=(PressureLoss("explicit lossless assumption", q(0, "Pa")),),
        )
    )
    assert r.required_source_pressure_pa == 100000
    assert r.dissipated_mechanical_power_w == 0
    assert not hasattr(r, "shaft_power_w")


def test_dimensionally_compatible_non_si_unit_conversion():
    r = liquid_feed_budget(
        **inputs(
            source_pressure=Quantity(182, Unit("kPa", "kilopascal", PRESSURE, 1000))
        )
    )
    assert r.pressure_residual_pa == 0


@pytest.mark.parametrize(
    "field,unit",
    [
        ("mass_flow", "kg/s"),
        ("density", "kg/m3"),
        ("source_pressure", "Pa"),
        ("required_sink_pressure", "Pa"),
        ("outlet_area", "m2"),
    ],
)
@pytest.mark.parametrize("value", [0, -1, True])
def test_positive_contract(field, unit, value):
    with pytest.raises(InvalidInputError):
        liquid_feed_budget(**inputs(**{field: q(value, unit)}))


@pytest.mark.parametrize(
    "field",
    [
        "mass_flow",
        "density",
        "source_pressure",
        "required_sink_pressure",
        "outlet_area",
        "source_velocity",
        "gravitational_acceleration",
    ],
)
def test_incompatible_dimensions(field):
    with pytest.raises(DimensionError):
        liquid_feed_budget(**inputs(**{field: q(1, "m")}))


@pytest.mark.parametrize(
    "edits",
    [
        {"source_velocity": q(-1, "m/s")},
        {"gravitational_acceleration": q(-1, "m/s2")},
        {"mass_flow": 2},
        {"losses": ()},
        {"losses": []},
        {"losses": (PressureLoss("a", q(-1, "Pa")),)},
        {"losses": (PressureLoss("", q(0, "Pa")),)},
        {"losses": (PressureLoss("a", q(0, "Pa")), PressureLoss("a", q(0, "Pa")))},
        {"losses": (replace(PressureLoss("a", q(0, "Pa")), name="a" * 81),)},
        {"elevation_rise": q(-100, "m")},
        {"mass_flow": q(1e300, "kg/s")},
        {"density": q(1e-320, "kg/m3")},
        {"outlet_area": q(1e-300, "m2")},
        {"mass_flow": q(1e-300, "kg/s"), "density": q(1e300, "kg/m3")},
    ],
)
def test_explicit_admissibility_and_arithmetic_refusal(edits):
    with pytest.raises(InvalidInputError):
        liquid_feed_budget(**inputs(**edits))


def test_continuity_independent_inlets_outlets_and_cancellation():
    assert (
        steady_mass_residual(
            inlets=(q(2, "kg/s"), q(1, "kg/s")), outlets=(q(3, "kg/s"),)
        )
        == 0
    )
    assert steady_mass_residual(
        inlets=(q(2.1, "kg/s"),), outlets=(q(2, "kg/s"),)
    ) == pytest.approx(0.1, abs=1e-14)
    assert steady_mass_residual(
        inlets=(q(0.9, "kg/s"),), outlets=(q(1, "kg/s"),)
    ) == pytest.approx(-0.1, abs=1e-14)
    assert steady_mass_residual(
        inlets=(q(2.1, "kg/s"), q(0.9, "kg/s")), outlets=(q(2, "kg/s"), q(1, "kg/s"))
    ) == pytest.approx(0, abs=1e-14)


@pytest.mark.parametrize(
    "inlets,outlets",
    [
        ((), (q(1, "kg/s"),)),
        ((q(-1, "kg/s"),), (q(1, "kg/s"),)),
        ((q(1, "m"),), (q(1, "kg/s"),)),
        ((q(1e308, "kg/s"),) * 32, (q(0, "kg/s"),)),
    ],
)
def test_continuity_rejects_missing_negative_wrong_dimension_and_overflow(
    inlets, outlets
):
    with pytest.raises((InvalidInputError, DimensionError)):
        steady_mass_residual(inlets=inlets, outlets=outlets)


def test_traceable_model_identity_and_nonclaims():
    payload = PRESSURE_FED.to_canonical_dict()
    assert "3-12" in payload["source"]
    assert payload["numerical_method_dependency"] == "none"
    assert "No physical validation" in " ".join(payload["limitations"])
