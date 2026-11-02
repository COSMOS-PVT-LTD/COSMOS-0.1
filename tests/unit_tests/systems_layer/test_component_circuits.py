from copy import deepcopy
from types import SimpleNamespace

import pytest

from systems.contracts.geometry import GeometryContractError
from systems.geometry.component_circuits import assess_circuits


def topology_fixture():
    """Manufactured graph-only fixture; native/actual-port tests are separate."""
    ports=[];matches=[];pipes=[];parts=[]
    def port(key,part,kind,fluid="UNASSIGNED"):
        ports.append({"id":key,"part_id":part,"kind":kind,"fluid":fluid});return key
    def part(key,**values):
        result=SimpleNamespace(part_id=key,holes=[],cooling=None,**values);parts.append(result);return result
    def match(a,b):matches.append({"from":a,"to":b})
    for name in ("fs","os","return"):
        part(name)
        for end in ("a","b"):port(name+".end-"+end,name,"PIPE_END")
        pipes.append({"end_a":name+".end-a","end_b":name+".end-b"})
    for name in ("lower","upper"):
        part(name);port(name+".supply",name,"COOLING_HEADER_SUPPLY","COOLANT_UNASSIGNED")
        for i in range(3):port(name+".channel-"+str(i),name,"COOLING_HEADER_CHANNEL","COOLANT_UNASSIGNED")
    wall=part("wall");wall.cooling=SimpleNamespace(count=3)
    for i in range(3):
        for label,header in (("nozzle_inlet_connection","lower"),("upper_collector_connection","upper")):
            key=port("wall.channel-"+str(i)+"-"+label,"wall",label.upper(),"COOLANT_UNASSIGNED")
            match(key,header+".channel-"+str(i))
    part("head")
    plate=part("plate");plate.holes=[SimpleNamespace(role=fluid,axial_range=None) for fluid in ("fuel","oxidizer")]
    for i,fluid in enumerate(("fuel","oxidizer")):
        inlet=port("head."+fluid+"-in","head","MANIFOLD_INLET",fluid)
        outlet=port("head."+fluid+"-out","head","MANIFOLD_OUTLET",fluid)
        match(outlet,port("plate.port-"+str(i)+"-inlet","plate","INJECTOR_INLET",fluid))
        port("plate.port-"+str(i)+"-discharge","plate","INJECTOR_DISCHARGE",fluid)
        match("return.end-b" if fluid=="fuel" else "os.end-b",inlet)
    match("fs.end-a","lower.supply")
    match("return.end-a","upper.supply")
    inspection={"ports":ports,"matches":matches,"pipe_paths":pipes,
        "unconnected_ports":[{"port_id":key} for key in ("fs.end-b","os.end-a")]}
    return SimpleNamespace(parts=parts),inspection


def test_explicit_segregated_fuel_regeneration_and_direct_oxidizer_topology():
    plan,inspection=topology_fixture();before=deepcopy(inspection)
    result=assess_circuits(plan,inspection,"fs.end-b","os.end-a")
    assert result["topology_complete"] and not result["issues"]
    assert all(cut["separates_fuel_boundary_from_injectors"] for cut in result["required_cut_vertices"])
    assert set(result["assigned_ports"]["fuel"]).isdisjoint(result["assigned_ports"]["oxidizer"])
    assert result["pressure_closure"]=="NOT_CALCULATED" and result["seals"]=="NOT_ASSESSED"
    assert inspection==before


@pytest.mark.parametrize("mutation,expected",[
    ("cross","FUEL_OXIDIZER_CROSS_CONNECTION"),
    ("bypass","REGENERATIVE_OR_INJECTOR_ROUTE_BYPASS"),
    ("open","UNCONNECTED_INTERNAL_ENDS"),
    ("unreached","FUEL_INJECTOR_ARRAY_NOT_REACHED"),
    ("swap","OXIDIZER_REACHES_COOLING_CIRCUIT"),
    ("reverse","FUEL_ROUTE_NOT_NOZZLE_TO_UPPER_COLLECTOR"),
])
def test_geometric_completeness_rejects_crossed_bypassed_open_or_unassigned_routes(mutation,expected):
    plan,inspection=topology_fixture();fuel,ox="fs.end-b","os.end-a"
    if mutation=="cross":inspection["matches"].append({"from":"fs.end-a","to":"os.end-b"})
    if mutation=="bypass":inspection["matches"].append({"from":"fs.end-a","to":"return.end-b"})
    if mutation=="open":inspection["unconnected_ports"].append({"port_id":"return.end-a"})
    if mutation=="unreached":inspection["matches"]=[m for m in inspection["matches"] if m["from"]!="head.fuel-out"]
    if mutation=="swap":fuel,ox=ox,fuel
    if mutation=="reverse":
        for m in inspection["matches"]:
            if m["to"]=="lower.supply":m["to"]="upper.supply"
            elif m["to"]=="upper.supply":m["to"]="lower.supply"
    result=assess_circuits(plan,inspection,fuel,ox)
    assert not result["topology_complete"] and expected in result["issues"]


@pytest.mark.parametrize("fuel,ox",[("invented","os.end-a"),("fs.end-b","fs.end-b"),("lower.supply","os.end-a")])
def test_boundary_must_be_two_actual_unconnected_pipe_ends(fuel,ox):
    plan,inspection=topology_fixture()
    with pytest.raises(GeometryContractError):assess_circuits(plan,inspection,fuel,ox)
