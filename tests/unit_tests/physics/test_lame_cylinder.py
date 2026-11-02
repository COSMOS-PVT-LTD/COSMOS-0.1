"""Independent analytic checks of the bounded, pressure-only Lamé field."""
import math

import pytest

from core.exceptions import DimensionError, InvalidInputError
from physics.quantities import metre, pascal
from physics.solid_mechanics.pressure_vessels import cylinder, lame_closed_cylinder
from physics.solid_mechanics.stress import von_mises


def field(pi=5e5, po=1e5, a=.05, t=.006, r=None):
    return lame_closed_cylinder(pascal(pi), pascal(po), metre(a), metre(t),
                                station_radius=None if r is None else metre(r))


def test_exact_boundary_tractions_and_end_force():
    pi, po, a, b = 5e5, 1e5, .05, .056
    bore, outer = field(), field(r=b)
    assert bore.radial.to_si() == pytest.approx(-pi)
    assert outer.radial.to_si() == pytest.approx(-po)
    axial_force = bore.longitudinal.to_si() * math.pi * (b*b-a*a)
    assert axial_force == pytest.approx(math.pi*(pi*a*a-po*b*b))
    assert bore.hoop.to_si() > outer.hoop.to_si()
    assert bore.von_mises.to_si() > outer.von_mises.to_si()
    assert bore.radius_to_thickness < 10  # deliberately outside the thin-wall assumption
    assert bore.identity.model_id.endswith("lame_closed_ends")


def test_independent_exact_bore_solution_and_von_mises():
    value = field(pi=10, po=0, a=1, t=1)
    assert value.radial.to_si() == pytest.approx(-10)
    assert value.hoop.to_si() == pytest.approx(50/3)
    assert value.longitudinal.to_si() == pytest.approx(10/3)
    expected = von_mises(value.radial.to_si(), value.hoop.to_si(), value.longitudinal.to_si())
    assert value.von_mises.to_si() == pytest.approx(expected.to_si())


def test_radial_equilibrium_finite_difference():
    r, h = .053, 1e-7
    center, left, right = field(r=r), field(r=r-h), field(r=r+h)
    derivative = (right.radial.to_si()-left.radial.to_si())/(2*h)
    residual = derivative+(center.radial.to_si()-center.hoop.to_si())/r
    assert residual == pytest.approx(0, abs=.01)


def test_hydrostatic_and_pressure_offset_invariance():
    hydro = field(pi=8e5, po=8e5)
    for stress in (hydro.radial, hydro.hoop, hydro.longitudinal):
        assert stress.to_si() == pytest.approx(-8e5)
    assert hydro.von_mises.to_si() == 0
    base, offset = field(), field(pi=8e5, po=4e5)
    for key in ("radial", "hoop", "longitudinal"):
        assert getattr(offset, key).to_si() == pytest.approx(getattr(base, key).to_si()-3e5)
    assert offset.von_mises.to_si() == pytest.approx(base.von_mises.to_si())


def test_scaling_and_thin_wall_limit():
    assert field(pi=1e6, po=2e5).von_mises.to_si() == pytest.approx(2*field().von_mises.to_si())
    exact = field(pi=1e5, po=0, a=.05, t=5e-8)
    thin = cylinder(pascal(1e5), metre(.05), metre(5e-8))
    assert exact.hoop.to_si() == pytest.approx(thin.hoop.to_si(), rel=1e-6)
    assert exact.longitudinal.to_si() == pytest.approx(thin.longitudinal.to_si(), rel=1e-6)


def test_external_pressure_field_is_not_buckling_approval():
    value = field(pi=1e5, po=8e5)
    assert value.radial.to_si() == pytest.approx(-1e5)
    assert value.hoop.to_si() < 0
    assert "No buckling" in value.identity.limitations[0]


@pytest.mark.parametrize("kwargs", [{"pi": -1}, {"po": -1}, {"a": 0}, {"t": 0},
    {"r": .04}, {"r": .057}, {"pi": float("inf")}, {"r": float("nan")}])
def test_invalid_inputs_fail(kwargs):
    with pytest.raises(InvalidInputError):
        field(**kwargs)


def test_dimensions_are_enforced():
    with pytest.raises(DimensionError):
        lame_closed_cylinder(metre(1), pascal(0), metre(.05), metre(.006))
