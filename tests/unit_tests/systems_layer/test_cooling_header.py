"""Exact annular-header voids/ports; not thermal or joint qualification."""
import math

import numpy as np
import pytest

from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.geometry.component_sections import section
from tests.fixtures.component_geometry import model, plan


def test_header_disjoint_void_integrals_and_topological_expectation():
    p=plan("manifold.cooling_annular");part=p.parts[0];ref=PartReference(p,part)
    gross=math.pi*(.04**2-.015**2)*.013
    plenum=math.pi*(.034**2-.018**2)*.008
    inlet=math.pi*.003**2*.003
    outlets=4*.3*(.026**2-.022**2)/2*.002
    expected=gross-plenum-inlet-outlets
    assert ref.volume_m3==pytest.approx(expected,rel=1e-13)
    moment=gross*.013/2-plenum*.007-inlet*.0015-outlets*.012
    assert ref.centroid_m[0]==pytest.approx(moment/expected,rel=1e-13)
    assert part.euler==-10 and len(part.cavities)==5
    inlet_ring=.026
    assert ref.centroid_m[1:]==pytest.approx(-inlet*inlet_ring*np.array([math.cos(.2),math.sin(.2)])/expected,abs=1e-15)


def test_header_has_clear_gas_bore_real_sector_port_openings_and_retained_web():
    p=plan("manifold.cooling_annular");ref=PartReference(p,p.parts[0])
    assert ref.sdf([[.006,0.,0.]])[0]>0 # Unobstructed central gas bore.
    assert ref.sdf([[.006,.025,0.]])[0]>0 # Coolant plenum, not central bore.
    for cavity in p.parts[0].cavities[1:]:
        angle=cavity.sector[0]+cavity.sector[1]/2
        for x in (cavity.profile[0][0],cavity.profile[-1][0]):
            assert ref.sdf([[x,.024*math.cos(angle),.024*math.sin(angle)]])[0]>.0019
    assert ref.sdf([[.012,.024*math.cos(.7),.024*math.sin(.7)]])[0]<0 # Uncut cap ligament.
    assert np.abs(ref.sdf(ref.surface_samples())).max()<1e-12


def test_header_cap_and_plenum_section_areas_are_independent():
    p=plan("manifold.cooling_annular");gross=math.pi*(.04**2-.015**2)
    assert section(p,"body",.001)["area_m2"]==pytest.approx(gross-math.pi*.003**2)
    assert section(p,"body",.007)["area_m2"]==pytest.approx(gross-math.pi*(.034**2-.018**2))
    assert section(p,"body",.012)["area_m2"]==pytest.approx(gross-4*.3*(.026**2-.022**2)/2)


@pytest.mark.parametrize("key,value",[("bore_radius",.019),("port_inner",.017),("port_outer",.035),
    ("supply_hole_radius",.009),("width",1.6),("front_web",1e-7)])
def test_blind_or_overlapping_ports_or_unresolved_header_walls_reject(key,value):
    spec=model("manifold.cooling_annular");spec["features"][0]["parameters"][key]["value"]=value
    with pytest.raises(ValueError):compile_model(spec,"engine-component-bad-header","r","2026-10-21T00:00:00Z")
