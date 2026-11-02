import math

import pytest

from core.dimension import FORCE, LENGTH
from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI, Unit
from physics.solid_mechanics.bolted_joint import axial_bolt_group
from physics.solid_mechanics.seal_gland import nominal_face_gland

STIFFNESS=Unit("N/m","newton per metre",FORCE/LENGTH)


def group(**updates):
    values={"internal_pressure":Quantity(1e6,SI.get("Pa")),"external_pressure":Quantity(0,SI.get("Pa")),
        "effective_seal_radius":Quantity(.01,SI.get("m")),"additional_axial_force":Quantity(0,SI.get("N")),
        "bolt_count":4,"tensile_area":Quantity(1e-5,SI.get("m2")),"bolt_allowable":Quantity(200e6,SI.get("Pa")),
        "bolt_stiffness":Quantity(100,STIFFNESS),"member_stiffness":Quantity(300,STIFFNESS),
        "preload_min":Quantity(1000,SI.get("N")),"preload_max":Quantity(1200,SI.get("N")),"required_seating_force":Quantity(500,SI.get("N"))}
    return axial_bolt_group(**(values|updates))


def test_independent_pressure_force_spring_compatibility_and_axial_equilibrium():
    result=group();external=math.pi*.01**2*1e6
    assert result.separating_force_n==pytest.approx(external)
    assert result.stiffness_load_fraction==.25
    assert result.minimum_retained_clamp_n==pytest.approx(4000-.75*external)
    assert result.peak_bolt_load_n==pytest.approx(1200+.25*external/4)
    assert result.bolt_stress_pa==pytest.approx(result.peak_bolt_load_n/1e-5)
    assert (4*1000+.25*external)-result.minimum_retained_clamp_n==pytest.approx(external)
    assert (.25*external/4)/100==pytest.approx((.75*external/4)/300)
    assert result.passed_declared_screen


def test_pressure_offset_invariance_and_separation_never_returns_linear_stress():
    assert group(internal_pressure=Quantity(1.5e6,SI.get("Pa")),external_pressure=Quantity(.5e6,SI.get("Pa")))==group()
    separated=group(internal_pressure=Quantity(1e8,SI.get("Pa")))
    assert not separated.contact_retained and not separated.passed_declared_screen
    assert separated.bolt_stress_pa is None and separated.peak_bolt_load_n is None
    assert not group(required_seating_force=Quantity(5000,SI.get("N"))).passed_declared_screen
    assert not group(bolt_allowable=Quantity(1e6,SI.get("Pa"))).passed_declared_screen


@pytest.mark.parametrize("updates",[{"bolt_count":True},{"bolt_count":0},{"preload_min":Quantity(2000,SI.get("N"))},
    {"bolt_stiffness":Quantity(0,STIFFNESS)},{"effective_seal_radius":Quantity(0,SI.get("m"))}])
def test_invalid_group_inputs(updates):
    with pytest.raises(InvalidInputError):group(**updates)


def test_group_dimensions():
    with pytest.raises(DimensionError):group(tensile_area=Quantity(1,SI.get("m")))


def fit(scale=1.,**updates):
    values={"section_diameter":Quantity(.003*scale,SI.get("m")),"mean_radius":Quantity(.05*scale,SI.get("m")),
        "radial_width":Quantity(.004*scale,SI.get("m")),"depth":Quantity(.0024*scale,SI.get("m")),
        "squeeze_min":.15,"squeeze_max":.25,"fill_max":.85}
    return nominal_face_gland(**(values|updates))


def test_nominal_gland_closed_forms_and_scale_laws_no_material_claim():
    a,b=fit(),fit(2.)
    assert a.squeeze_fraction==pytest.approx(.2)
    assert a.seal_volume_m3==pytest.approx(2*math.pi**2*.05*(.003/2)**2)
    assert a.fill_fraction==pytest.approx(math.pi*.003**2/(4*.004*.0024))
    assert a.passed_declared_geometry
    assert b.squeeze_fraction==pytest.approx(a.squeeze_fraction) and b.fill_fraction==pytest.approx(a.fill_fraction)
    assert b.gland_volume_m3==pytest.approx(8*a.gland_volume_m3)
    assert not fit(depth=Quantity(.004,SI.get("m"))).passed_declared_geometry
    assert not fit(fill_max=.5).passed_declared_geometry


@pytest.mark.parametrize("updates",[{"squeeze_max":1.},{"fill_max":True},{"squeeze_min":.5},
    {"depth":Quantity(0,SI.get("m"))},{"mean_radius":Quantity(.001,SI.get("m"))}])
def test_invalid_gland_criteria(updates):
    with pytest.raises(InvalidInputError):fit(**updates)
