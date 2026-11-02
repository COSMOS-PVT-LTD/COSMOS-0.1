import math

import pytest

from systems.geometry.component_sections import section
from tests.fixtures.component_geometry import plan


@pytest.mark.parametrize("kind",["profile.wall","cooling.axial_sector","injector.showerhead","injector.doublet","injector.triplet","injector.coaxial","injector.pintle"])
def test_exact_sections_integrate_to_independent_part_volumes(kind):
    from systems.geometry.component_reference import PartReference
    value=plan(kind)
    # Simpson is exact for piecewise quadratic ring/sector/ellipse areas.
    for part in value.parts:
        total=0.
        for a,b in zip(part.profile,part.profile[1:],strict=False):
            x0,x1=a[0],b[0]; h=(x1-x0)/4
            values=[section(value,part.part_id,x0+h*(i+.5))["area_m2"] for i in range(4)]
            # Two-point Gauss integrates each quadratic segment exactly.
            mid=(x0+x1)/2; delta=(x1-x0)/(2*math.sqrt(3))
            total+=(x1-x0)/2*sum(section(value,part.part_id,x)["area_m2"] for x in (mid-delta,mid+delta))
            assert all(v>0 for v in values)
        assert total==pytest.approx(PartReference(value,part).volume_m3,rel=1e-10)


@pytest.mark.parametrize("x",[0.,.08,float('nan'),float('inf'),True])
def test_tangent_outside_nonfinite_or_implicit_section_is_refused(x):
    with pytest.raises(ValueError): section(plan(),"body",x)


def test_open_cooling_port_interior_is_not_a_retained_metal_end_surface():
    import numpy as np

    from systems.geometry.component_reference import PartReference
    value=plan("cooling.axial_sector");part=value.parts[0];c=part.cooling
    a=c.phase_rad+c.width_rad/2
    for x,ri,_ in (part.profile[0],part.profile[-1]):
        radius=ri+c.hot_ligament+c.depth/2
        assert PartReference(value,part).sdf(np.array([[x,radius*math.cos(a),radius*math.sin(a)]]))[0]>0
