"""Analytical software verification; none of these tests is hot-fire validation."""

import math
from dataclasses import replace

import pytest

from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.compressible_flow.bell_nozzle import bell_contour, flow_stations
from physics.exceptions import OutOfRangeError
from physics.heat_transfer.film_cooling import effectiveness, film_adiabatic_temperature
from physics.heat_transfer.regenerative import (
    CoolingInputs,
    GasWallStation,
    regenerative_cooling,
)
from physics.injectors.orifice import bipropellant_mass_split, liquid_orifice
from physics.quantities import kelvin, metre, pascal
from physics.si import (
    UNIT_DYNAMIC_VISCOSITY,
    UNIT_HTC,
    UNIT_SPECIFIC_HEAT,
    UNIT_THERMAL_CONDUCTIVITY,
)


def q(value, unit):
    return Quantity(value, SI.get(unit))


def test_orifice_independent_reference_and_roundtrip():
    result = liquid_orifice(
        q(1, "kg/s"),
        q(1000, "kg/m3"),
        pascal(1e6),
        Quantity(0.001, UNIT_DYNAMIC_VISCOSITY),
        0.7,
        100,
    )
    expected = 1 / (0.7 * math.sqrt(2 * 1000 * 1e6))
    assert result.total_area_m2 == pytest.approx(expected)
    assert result.diameter_m == pytest.approx(math.sqrt(4 * expected / (math.pi * 100)))
    assert 0.7 * result.total_area_m2 * math.sqrt(2 * 1000 * 1e6) == pytest.approx(1)
    assert result.velocity_m_s == pytest.approx(0.7 * math.sqrt(2 * 1e6 / 1000))
    ox, fuel = bipropellant_mass_split(q(3.3, "kg/s"), 2.3)
    assert ox.to_si() == pytest.approx(2.3)
    assert fuel.to_si() == pytest.approx(1)


@pytest.mark.parametrize(
    "cd,count",
    [(0, 100), (1.1, 100), (math.nan, 100), (0.7, 1.5), (0.7, True), (0.7, 0)],
)
def test_orifice_rejects_invalid_cd_counts(cd, count):
    with pytest.raises(InvalidInputError):
        liquid_orifice(
            q(1, "kg/s"),
            q(1000, "kg/m3"),
            pascal(1e6),
            Quantity(0.001, UNIT_DYNAMIC_VISCOSITY),
            cd,
            count,
        )


def test_orifice_dimensional_contract():
    with pytest.raises(DimensionError):
        liquid_orifice(
            metre(1),
            q(1000, "kg/m3"),
            pascal(1e6),
            Quantity(0.001, UNIT_DYNAMIC_VISCOSITY),
            0.7,
            100,
        )


def test_bell_nasa_sp125_worked_geometry_reference():
    # SP-125 printed page 98: Rt=12.45 in, epsilon=14, 80% bell,
    # theta_n=27.4 deg, theta_e=9.8 deg, Rb/Rt=.382; Ln ~=102.4 in.
    rows = bell_contour(metre(12.45 * 0.0254), 14, 0.8, 27.4, 9.8, 0.382, 101)
    assert rows[0].x_m == 0
    assert rows[0].wall_angle_deg == 0
    assert rows[-1].x_m / 0.0254 == pytest.approx(102.4, abs=0.2)
    assert rows[-1].radius_m / 0.0254 == pytest.approx(46.7, abs=0.2)
    assert rows[-1].area_ratio == pytest.approx(14)
    assert rows[-1].wall_angle_deg == pytest.approx(9.8)
    assert len(rows) == 101
    assert rows[19].wall_angle_deg == pytest.approx(27.4)
    stations = flow_stations(rows, pascal(5e6), kelvin(3000), 1.2)
    assert stations[0].mach == 1
    assert stations[-1].pressure_pa < stations[0].pressure_pa


@pytest.mark.parametrize(
    "kwargs",
    [
        {"expansion_ratio": 1},
        {"length_fraction": 0},
        {"start_angle_deg": 5},
        {"blend_radius_ratio": 100},
        {"point_count": True},
        {"point_count": 3},
        {"exit_angle_deg": math.nan},
    ],
)
def test_bell_invalid_geometry(kwargs):
    inputs = {
        "throat_radius": metre(0.02),
        "expansion_ratio": 8,
        "length_fraction": 0.8,
        "start_angle_deg": 30,
        "exit_angle_deg": 8,
        "blend_radius_ratio": 0.382,
        "point_count": 101,
    }
    with pytest.raises(InvalidInputError):
        bell_contour(**(inputs | kwargs))


def test_film_mixing_reference_and_limits():
    args = {
        "boundary_layer_thickness": metre(0.001),
        "slot_height": metre(0.001),
        "blowing_ratio": 1,
        "heat_capacity_ratio": 0.5,
    }
    eta = effectiveness(**args)
    assert eta == pytest.approx(1 / (1 + 0.5 * 7 / 8))
    assert effectiveness(**(args | {"blowing_ratio": 2})) > eta
    assert effectiveness(**(args | {"boundary_layer_thickness": metre(0.002)})) < eta
    taw = film_adiabatic_temperature(kelvin(3000), kelvin(300), eta)
    assert 300 < taw.to_si() < 3000
    with pytest.raises(DimensionError):
        effectiveness(**(args | {"slot_height": pascal(1)}))


def cooling_case(count=11):
    inputs = CoolingInputs(
        q(1, "kg/s"),
        kelvin(300),
        pascal(8e6),
        q(800, "kg/m3"),
        Quantity(0.0005, UNIT_DYNAMIC_VISCOSITY),
        Quantity(0.6, UNIT_THERMAL_CONDUCTIVITY),
        Quantity(2500, UNIT_SPECIFIC_HEAT),
        metre(0.001),
        metre(0.001),
        metre(0.0005),
        60,
        metre(0.001),
        Quantity(20, UNIT_THERMAL_CONDUCTIVITY),
        kelvin(200),
        kelvin(600),
        kelvin(800),
        pascal(1e5),
        "throat_to_exit",
    )
    stations = tuple(
        GasWallStation(
            metre(0.1 * i / (count - 1)),
            metre(0.02),
            Quantity(1000, UNIT_HTC),
            kelvin(1000),
        )
        for i in range(count)
    )
    return inputs, stations


def test_regen_matches_exact_constant_profile_and_pressure_reference():
    inputs, stations = cooling_case()
    result = regenerative_cooling(stations, inputs)
    re = 1 * 0.001 / (60 * 1e-6 * 0.0005)
    pr = 0.0005 * 2500 / 0.6
    hc = 0.023 * re**0.8 * pr**0.4 * 0.6 / 0.001
    area = 2 * math.pi * 0.02 * 0.1
    resistance = 1 / 1000 + 0.001 / 20 + (2 * math.pi * 0.02 / (60 * 0.001)) / hc
    expected = 1000 - 700 * math.exp(-area / (resistance * 2500))
    expected_loss = (
        0.3164 * re**-0.25 * 0.1 / 0.001 * 800 * (1 / (800 * 60 * 1e-6)) ** 2 / 2
    )
    assert result.outlet_temperature_k == pytest.approx(expected)
    assert result.total_pressure_loss_pa == pytest.approx(expected_loss)
    assert result.total_heat_w == pytest.approx(2500 * (expected - 300))
    assert abs(result.energy_residual_w) < 1e-7
    for row in result.segments:
        assert (
            row.hot_wall_temperature_k
            >= row.cold_wall_temperature_k
            > row.coolant_in_temperature_k
        )
        assert row.peak_hot_wall_temperature_k >= row.hot_wall_temperature_k


@pytest.mark.parametrize(
    "change",
    [
        "low_re",
        "high_re",
        "packing",
        "pressure",
        "property_window",
        "wall_limit",
        "bad_direction",
        "thick_wall",
    ],
)
def test_regen_fails_closed_for_invalid_applicability(change):
    inputs, stations = cooling_case()
    overrides = {
        "low_re": {"mass_flow": q(0.01, "kg/s")},
        "high_re": {"mass_flow": q(10, "kg/s")},
        "packing": {"channel_count": 1000},
        "pressure": {"inlet_pressure": pascal(100001)},
        "property_window": {"max_temperature": kelvin(301)},
        "wall_limit": {"max_wall_temperature": kelvin(300)},
        "bad_direction": {"direction": "guess"},
        "thick_wall": {"wall_thickness": metre(0.01)},
    }
    with pytest.raises((OutOfRangeError, InvalidInputError)):
        regenerative_cooling(stations, replace(inputs, **overrides[change]))


def test_constant_profile_partition_invariance_and_direction():
    coarse, stations = cooling_case(2)
    dense, more = cooling_case(101)
    a, b = regenerative_cooling(stations, coarse), regenerative_cooling(more, dense)
    assert a.total_heat_w == pytest.approx(b.total_heat_w, rel=1e-12)
    assert a.total_pressure_loss_pa == pytest.approx(
        b.total_pressure_loss_pa, rel=1e-12
    )
    reverse = regenerative_cooling(more, replace(dense, direction="exit_to_throat"))
    assert reverse.outlet_temperature_k == pytest.approx(b.outlet_temperature_k)
    assert reverse.segments[0].x_m > reverse.segments[-1].x_m
