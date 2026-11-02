import math
from copy import deepcopy

import pytest

from systems.contracts.geometry import GeometryContractError
from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import compile_model
from systems.geometry.pipe_routes import append_engine_pipes
from tests.fixtures.component_geometry import model


def compile_spec(spec):
    return compile_model(spec,"engine-component-pipe-route-test","synthetic","2026-10-21T00:00:00+00:00")


def fixture():
    """Synthetic separate heads for routing math, not a complete engine fixture."""
    spec=model("manifold.dual_annular");spec["features"][0]["id"]="head";spec["outputs"]=["head"]
    head=spec["features"][0]["parameters"]
    head["fuel_inlet_phase"]["value"]=0.;head["oxidizer_inlet_phase"]["value"]=math.pi
    parameters=model("manifold.cooling_annular")["features"][0]["parameters"]
    for key,value in {"bore_radius":.03,"outer_radius":.06,"plenum_inner":.033,"plenum_outer":.054,
        "port_inner":.038,"port_outer":.042,"supply_hole_radius":.0015,"supply_phase":0.}.items():parameters[key]["value"]=value
    for name in ("upper","lower"):
        if name=="lower":spec["frames"].append({"id":name,"parent":"world","origin":[{"value":v,"unit":"m"} for v in (.3,0.,0.)],"rotation":[-1.,0.,0.,0.,1.,0.,0.,0.,-1.]})
        spec["features"].append({"id":name,"operation":"manifold.cooling_annular","frame":"world" if name=="upper" else name,"depends_on":[],"parameters":deepcopy(parameters)})
        spec["outputs"].append(name)
    inspection=inspect_interfaces(compile_spec(spec),1e-6)
    proposal={"scope":"ISOLATED_GEOMETRY_HYPOTHESIS_NOT_INSTALLED_ENGINE_INPUTS","source":"Synthetic routing fixture only",
        "lower_header_port":"lower.port-0","upper_header_port":"upper.port-0","fuel_manifold_port":"head.port-0",
        "oxidizer_manifold_port":"head.port-4","wall_thickness_m":.0012,"return_bend_radius_m":.012,
        "return_stub_length_m":.025,"fuel_supply_length_m":.08,"oxidizer_supply_length_m":.08}
    return spec,inspection,proposal


def test_routing_derives_bores_and_ports_from_exact_source_without_mutation():
    spec,inspection,proposal=fixture();before=deepcopy(spec)
    result,bindings=append_engine_pipes(spec,inspection,proposal)
    current=inspect_interfaces(compile_spec(result),1e-6)
    assert spec==before and len(current["pipe_paths"])==7
    assert sum(m["opening"]=="MATCHING_PIPE_CIRCLES" for m in current["matches"])==8
    assert set(bindings.values())<={p["port_id"] for p in current["unconnected_ports"]}
    assert {p["bore_radius_m"] for p in current["pipe_paths"]}=={.0015,.002}


@pytest.mark.parametrize("mutation",["stale","missing","radius","orientation","unknown"])
def test_no_stale_port_table_guessed_reducer_arbitrary_orientation_or_hidden_dimension(mutation):
    spec,inspection,proposal=fixture()
    if mutation=="stale":inspection["source_graph_id"]="components-stale"
    if mutation=="missing":proposal["fuel_manifold_port"]="invented"
    if mutation=="radius":proposal["return_bend_radius_m"]=.1
    if mutation=="orientation":next(p for p in inspection["ports"] if p["id"]=="upper.port-0")["normal"]=[0.,1.,0.]
    if mutation=="unknown":proposal["balancing_loss"]=1.
    with pytest.raises(GeometryContractError):append_engine_pipes(spec,inspection,proposal)
