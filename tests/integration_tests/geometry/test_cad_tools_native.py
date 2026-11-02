"""Explicitly configured real OCCT tests, independent known-solid expectations."""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[3]


def native(code):
    interpreter=os.environ.get("CAD_TOOLS_PYTHON")
    if not interpreter:pytest.skip("Explicit pinned CAD_TOOLS_PYTHON native campaign required")
    p=subprocess.run([interpreter,"-c",code],cwd=ROOT,capture_output=True,timeout=30,check=False,env={**os.environ,"PYTHONPATH":str(ROOT),"OMP_NUM_THREADS":"1"})
    assert p.returncode==0,p.stderr.decode()[-2000:]
    return json.loads(p.stdout)


BASE='''from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Pnt
from plugins.geometry.workers.cad_inspection_worker import clearance,drawing,properties
import json
a=BRepPrimAPI_MakeBox(10,10,10).Shape()
request=dict(pair=["a","b"],linear_tolerance_m=1e-8,volume_resolution_m3=1e-15,required_clearance_m=.001)
'''


@pytest.mark.parametrize("x,required,expected,distance",[(12,.001,"SATISFIED",.002),(12,.003,"BELOW_REQUIRED",.002),(12,.002,"INDETERMINATE",.002),(10,.001,"INDETERMINATE",0),(8,.001,"FAIL_INTERFERENCE",0),(10.000005,.001,"INDETERMINATE",5e-9)])
def test_native_box_pair_classification(x,required,expected,distance):
    result=native(BASE+f'b=BRepPrimAPI_MakeBox(gp_Pnt({x},0,0),10,10,10).Shape();request["required_clearance_m"]={required};print(json.dumps(clearance({{"a":a,"b":b}},request)))')
    assert result["clearance_status"]==expected
    assert result["minimum_distance_m"]==pytest.approx(distance,abs=1e-10)
    if x==8:assert result["intersection_volume_m3"]==pytest.approx(2e-7)


def test_contained_solid_is_interference_not_surface_clearance():
    result=native(BASE+'b=BRepPrimAPI_MakeBox(gp_Pnt(2,2,2),2,2,2).Shape();print(json.dumps(clearance({"a":a,"b":b},request)))')
    assert result["relation"]=="INTERFERENCE";assert result["intersection_volume_m3"]==pytest.approx(8e-9)


def test_overlapping_bounding_boxes_do_not_establish_solid_interference():
    result=native(BASE+'''from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
a=BRepAlgoAPI_Cut(BRepPrimAPI_MakeCylinder(10,10).Shape(),BRepPrimAPI_MakeCylinder(8,10).Shape()).Shape()
b=BRepPrimAPI_MakeCylinder(7,10).Shape()
request["required_clearance_m"]=.0005
print(json.dumps(clearance({"a":a,"b":b},request)))''')
    assert result["relation"]=="DISJOINT";assert result["minimum_distance_m"]==pytest.approx(.001);assert result["intersection_volume_m3"]==0


def test_small_intersection_is_not_relabelled_as_disjoint():
    result=native(BASE+'b=BRepPrimAPI_MakeBox(gp_Pnt(8,0,0),10,10,10).Shape();request["volume_resolution_m3"]=1e-6;print(json.dumps(clearance({"a":a,"b":b},request)))')
    assert result["relation"]=="UNRESOLVED_SMALL_INTERSECTION";assert result["clearance_status"]=="INDETERMINATE"


def test_clearance_witnesses_are_actual_source_coordinate_points():
    result=native(BASE+'b=BRepPrimAPI_MakeBox(gp_Pnt(12,0,0),10,10,10).Shape();print(json.dumps(clearance({"a":a,"b":b},request)))')
    import math
    for pair in result["witnesses"]:assert math.dist(pair["a_m"],pair["b_m"])==pytest.approx(.002)


def test_native_hlr_returns_three_views_native_bounds_and_hidden_edges():
    result=native(BASE+'print(json.dumps(drawing({"a":a},{"part_id":"a","curve_deflection_m":1e-5})))')
    assert len(result["views"])==3;assert result["bounds_m"]==pytest.approx([0,0,0,.01,.01,.01])
    assert all(any(l["hidden"] for l in v["lines"]) and any(not l["hidden"] for l in v["lines"]) for v in result["views"])


def test_native_drawing_pdf_and_svg_include_source_scale_and_draft_status():
    result=native(BASE+'''from systems.geometry.manufacturing_drawing import svg,pdf
d=drawing({"a":a},{"part_id":"a","curve_deflection_m":1e-5})
m=dict(title="Software fixture",number="QA1",revision="A",author="QA",material="NOT SPECIFIED",process="NOT SPECIFIED",tolerance_note="NOT SPECIFIED",finish_note="NOT SPECIFIED",parameters=[],scale_denominator=1,job_id="job-fixture",source_sha256="a"*64,model_commit_id="model-fixture")
s=svg(d,m);p=pdf(d,m)
print(json.dumps(dict(svg=s.decode(),pdf_magic=p[:5].decode(),pdf_bytes=len(p))))''')
    assert result["pdf_magic"]=="%PDF-";assert result["pdf_bytes"]>2000
    assert "UNRELEASED" in result["svg"] and "job-fixture" in result["svg"] and "10.000 mm" in result["svg"]
    import xml.etree.ElementTree as ET
    ET.fromstring(result["svg"])


def test_oversize_drawing_refuses_silent_rescaling():
    result=native(BASE+'''from systems.geometry.manufacturing_drawing import layout
d=drawing({"a":a},{"part_id":"a","curve_deflection_m":1e-5})
try:layout(d,{"scale_denominator":.01});result=False
except ValueError:result=True
print(json.dumps(result))''')
    assert result
