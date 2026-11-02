from copy import deepcopy

import pytest

from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import IDENTITY, compile_model
from systems.projects.authority import StoreUnavailable
from tests.fixtures.component_geometry import model, plan


def distributor(phase_offset=0.):
    value=model("manifold.dual_annular"); head=value["features"][0]["parameters"]
    plate=deepcopy(model("injector.biprop_radial_doublet")["features"][0]);plate["id"]="plate";plate["frame"]="plate-frame"
    for key in ("ring_radius","separation","count","fuel_hole_radius","oxidizer_hole_radius","phase"):
        plate["parameters"][key]=deepcopy(head[key])
    plate["parameters"]["phase"]["value"]+=phase_offset
    end=sum(head[k]["value"] for k in ("back_web","plenum_length","front_web"))
    value["frames"].append({"id":"plate-frame","parent":"world","origin":[{"value":v,"unit":"m"} for v in (end,0.,0.)],"rotation":list(IDENTITY)})
    value["features"].append(plate);value["outputs"].append("plate")
    return compile_model(value,"engine-component-interface-test","r1","2026-10-21T00:00:00Z")


def test_exact_isolated_manifold_to_radial_plate_mating_and_turn_loss_nonclaim():
    value=inspect_interfaces(distributor(),1e-6)
    assert len(value["ports"])==20 and len(value["matches"])==6
    assert {r["fluid"] for r in value["matches"]}=={"fuel","oxidizer"}
    assert all(r["center_mismatch_m"]<1e-15 and r["common_area_m2"]>0 for r in value["matches"])
    assert all(r["turn_entrance_loss"]=="NOT_CALCULATED" and r["seal_status"]=="NOT_ASSESSED" for r in value["matches"])
    assert len(value["unconnected_ports"])==2 and all(r["kind"]=="MANIFOLD_INLET" for r in value["unconnected_ports"])
    assert not value["geometry_route_complete"] and value["pressure_closure"]=="NOT_CALCULATED"


def test_equal_counts_do_not_hide_wrong_positions_or_assume_missing_pipes():
    value=inspect_interfaces(distributor(.2),1e-6)
    assert not value["matches"] and len(value["unconnected_ports"])==14
    assert "Fuel return pipe to injector manifold" in value["required_unimplemented_geometry"]


def test_coolant_channels_have_real_end_openings_not_implicitly_fuel_or_plenums():
    value=inspect_interfaces(plan("cooling.axial_sector"),1e-6)
    assert len(value["ports"])==8 and not value["matches"]
    assert {p["fluid"] for p in value["ports"]}=={"COOLANT_UNASSIGNED"}
    assert {p["kind"] for p in value["ports"]}=={"UPPER_COLLECTOR_CONNECTION","NOZZLE_INLET_CONNECTION"}
    assert all(p["aperture"]["kind"]=="ANNULAR_SECTOR" and p["axial_aperture_area_m2"]>0 for p in value["ports"])


def test_flange_geometry_is_not_a_seal_or_bolt_acceptance():
    value=inspect_interfaces(plan("interface.bolted_flange"),1e-6)
    assert value["flange_candidates"][0]["bolt_count"]==6
    assert value["flange_candidates"][0]["joint_status"]=="SEAL_PRELOAD_MATERIAL_ATTACHMENT_NOT_ASSESSED"


def test_two_actual_headers_match_both_channel_end_shapes_after_proper_reversal():
    value=model("cooling.axial_sector");q=lambda v,u="m":{"value":v,"unit":u}
    for name,end,radius,rotation,phase in (("upper",-.013,.02,list(IDENTITY),.1),
        ("lower",.093,.015,[-1.,0.,0.,0.,1.,0.,0.,0.,-1.],-.4)):
        header=deepcopy(model("manifold.cooling_annular")["features"][0]);header["id"]=name;header["frame"]=name
        header["parameters"].update(bore_radius=q(radius),plenum_inner=q(radius+.0005),port_inner=q(radius+.001),port_outer=q(radius+.002),phase=q(phase,"rad"))
        value["features"].append(header);value["outputs"].append(name)
        value["frames"].append({"id":name,"parent":"world","origin":[q(end),q(0.),q(0.)],"rotation":rotation})
    plan=compile_model(value,"engine-component-header-interface","r","2026-10-21T00:00:00Z")
    result=inspect_interfaces(plan,1e-6)
    assert len(result["matches"])==8 and len(result["unconnected_ports"])==2
    assert all(m["opening"]=="MATCHING_WORLD_ANNULAR_SECTORS" and m["boundary_corner_mismatch_m"]<1e-15 for m in result["matches"])
    assert all(p["kind"]=="COOLING_HEADER_SUPPLY" for p in result["unconnected_ports"])
    assert all(m["fluid"]=="COOLANT_UNASSIGNED" for m in result["matches"])
    assert not any("Nozzle-end inlet plenum" in v for v in result["required_unimplemented_geometry"])
    assert not result["geometry_route_complete"] and result["pressure_closure"]=="NOT_CALCULATED"


@pytest.mark.parametrize("tol",[0,-1,float("nan"),.01,True])
def test_explicit_numerical_tolerance_bounds(tol):
    with pytest.raises(ValueError):inspect_interfaces(distributor(),tol)


def test_old_loaded_methods_cannot_claim_new_source_hashes(monkeypatch):
    from systems.geometry import component_interfaces
    monkeypatch.setattr(component_interfaces,"methods",lambda:{"changed":"0"*64})
    with pytest.raises(StoreUnavailable):component_interfaces.inspect_interfaces(distributor(),1e-6)
