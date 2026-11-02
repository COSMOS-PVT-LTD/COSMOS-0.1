import json
import math
from copy import deepcopy

import numpy as np
import pytest

from core.serialization import canonical_json_dumps
from systems.contracts.geometry import GeometryContractError
from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.geometry.component_sections import section
from tests.fixtures.component_geometry import model, plan


def compile_spec(spec):
    return compile_model(spec,"engine-component-pipe-test","synthetic","2026-10-21T00:00:00+00:00")


@pytest.mark.parametrize("kind",["pipe.circular","pipe.elbow"])
def test_pipe_has_positive_annular_volume_and_no_fictitious_cap_across_bore(kind):
    value=plan(kind); part=value.parts[0]; ref=PartReference(value,part); pipe=part.pipe
    assert pipe is not None and part.euler==0
    length=pipe.length if pipe.length is not None else pipe.bend_radius*pipe.angle_rad
    assert ref.volume_m3==pytest.approx(math.pi*(pipe.outer_radius**2-pipe.bore_radius**2)*length,rel=1e-13)
    assert ref.sdf([[0.,0.,0.]])[0]>0  # Start opening interior is NOT metal/end cap.
    assert np.abs(ref.sdf(ref.surface_samples())).max()<1e-13


def test_elbow_reference_uses_volume_centroid_not_centerline_centroid():
    value=plan("pipe.elbow"); pipe=value.parts[0].pipe; ref=PartReference(value,value.parts[0])
    radius=pipe.bend_radius; angle=pipe.angle_rad; j=(pipe.outer_radius**2+pipe.bore_radius**2)/4
    expected=np.array([(radius**2+j)*(1-math.cos(angle))/(radius*angle),radius-(radius**2+j)*math.sin(angle)/(radius*angle),0.])
    assert ref.centroid_m==pytest.approx(expected,abs=1e-14)
    assert abs(ref.centroid_m[0]-radius*(1-math.cos(angle))/angle)>1e-5
    # Independent volume-weighted Gaussian integration over annulus and arc.
    nodes,weights=np.polynomial.legendre.leggauss(24)
    phis=(nodes+1)*angle/2; rs=(nodes+1)*(pipe.outer_radius-pipe.bore_radius)/2+pipe.bore_radius
    total=0.; moment=np.zeros(3)
    for phi,wphi in zip(phis,weights):
        for r,wr in zip(rs,weights):
            for alpha in np.arange(64)*2*math.pi/64:
                d=radius+r*math.cos(alpha)
                weight=wphi*wr*r*d
                total+=weight;moment+=weight*np.array([d*math.sin(phi),radius-d*math.cos(phi),r*math.sin(alpha)])
    assert moment/total==pytest.approx(expected,abs=1e-13)


def test_rotated_translated_elbow_bounds_and_surface_are_source_exact():
    spec=model("pipe.elbow"); c,s=math.cos(.6),math.sin(.6); a,b=math.cos(.4),math.sin(.4)
    rotation=np.array([[a,-b,0.],[b,a,0.],[0.,0.,1.]])@np.array([[c,0.,s],[0.,1.,0.],[-s,0.,c]])
    spec["frames"].append({"id":"mount","parent":"world","origin":[{"value":x,"unit":"m"} for x in (.13,-.2,.11)],"rotation":rotation.flatten().tolist()})
    spec["features"][0]["frame"]="mount"
    value=compile_spec(spec); ref=PartReference(value,value.parts[0]); samples=ref.surface_samples(); bounds=ref.bounds_m
    assert np.all(samples>=bounds[:3]-1e-14) and np.all(samples<=bounds[3:]+1e-14)
    assert np.abs(ref.sdf(samples)).max()<1e-13
    assert ref.centroid_m==pytest.approx(rotation@PartReference(plan("pipe.elbow"),plan("pipe.elbow").parts[0]).centroid_m+np.array([.13,-.2,.11]))
    with pytest.raises(GeometryContractError,match="curve-normal"):
        section(value,"body",.01)


@pytest.mark.parametrize("update",[{"wall_thickness":{"value":0.,"unit":"m"}},
    {"wall_thickness":{"value":1e-5,"unit":"m"}},
    {"bend_radius":{"value":.006,"unit":"m"}},
    {"angle":{"value":math.pi,"unit":"rad"}},
    {"angle":{"value":90.,"unit":"deg"}},
    {"bend_loss":{"value":1.,"unit":"1"}}])
def test_no_unresolved_wall_tight_radius_unsupported_angle_or_inferred_loss(update):
    spec=deepcopy(model("pipe.elbow"));spec["features"][0]["parameters"].update(update)
    with pytest.raises(GeometryContractError):compile_spec(spec)


@pytest.mark.parametrize("angle",[math.pi/12,math.pi/2])
def test_closed_angle_limits_survive_frozen_core_canonical_save_reload(angle):
    spec=model("pipe.elbow");spec["features"][0]["parameters"]["angle"]["value"]=angle
    original=compile_spec(spec)
    restored=compile_spec(json.loads(canonical_json_dumps(spec)))
    assert restored.parts[0].pipe.angle_rad==json.loads(canonical_json_dumps({"angle":angle}))["angle"]
    assert PartReference(restored,restored.parts[0]).volume_m3==pytest.approx(PartReference(original,original.parts[0]).volume_m3,rel=1e-14)


@pytest.mark.parametrize("angle",[math.pi/12-1e-12,math.pi/2+1e-12])
def test_serialization_boundary_fix_does_not_accept_outside_domain_angles(angle):
    spec=model("pipe.elbow");spec["features"][0]["parameters"]["angle"]["value"]=angle
    with pytest.raises(GeometryContractError):compile_spec(json.loads(canonical_json_dumps(spec)))
