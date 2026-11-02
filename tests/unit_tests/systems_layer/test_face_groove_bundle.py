import math
from copy import deepcopy

import pytest

from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from tests.fixtures.component_geometry import model


def compile(spec):return compile_model(spec,"engine-component-groove-bundle-test","synthetic","2026-10-21T00:00:00Z")


def test_bundle_equals_sequential_cuts_in_volume_centroid_topology_and_semantics():
    spec=model("five-grooved-bolted-injector");bundle=compile(spec);p=bundle.parts[0]
    single=deepcopy(spec);feature=single["features"].pop();source=feature["depends_on"][0]
    parameters=feature["parameters"]
    for index in range(5):
        name="individual-"+str(index)
        single["features"].append({"id":name,"operation":"interface.face_groove","frame":"world","depends_on":[source],
            "parameters":{key:parameters[key+str(index)] for key in ("inner_radius","outer_radius","depth","face")}})
        source=name
    single["outputs"]=[source];sequential=compile(single);part=sequential.parts[0]
    reference=PartReference(bundle,p);expected=PartReference(sequential,part)
    assert reference.volume_m3==pytest.approx(expected.volume_m3,rel=1e-14)
    assert reference.centroid_m==pytest.approx(expected.centroid_m,abs=1e-14)
    assert p.holes==part.holes and p.euler==part.euler
    assert len(p.cavities)==5 and len({c.role for c in p.cavities})==5
    original=compile({**spec,"features":spec["features"][:-1],"outputs":["bolted"]})
    removed=math.fsum(math.pi*(c.profile[0][2]**2-c.profile[0][1]**2)*(c.profile[-1][0]-c.profile[0][0]) for c in p.cavities)
    assert reference.volume_m3==pytest.approx(PartReference(original,original.parts[0]).volume_m3-removed,rel=1e-14)


@pytest.mark.parametrize("key,value",[("count",0),("count",6),("count",True),("depth4",.004),("face2",0),("inner_radius2",.019)])
def test_bundle_rejects_capacity_blind_floor_invalid_face_and_overlapping_grooves(key,value):
    spec=model("five-grooved-bolted-injector");spec["features"][-1]["parameters"][key]["value"]=value
    with pytest.raises(ValueError):compile(spec)


def test_opposed_same_radius_grooves_need_a_resolved_common_blind_floor():
    spec=model("five-grooved-bolted-injector");p=spec["features"][-1]["parameters"]
    for key in ("inner_radius","outer_radius"):p[key+"4"]=deepcopy(p[key+"0"])
    p["depth0"]["value"]=.002;p["depth4"]["value"]=.002
    with pytest.raises(ValueError,match="floor/land"):compile(spec)
