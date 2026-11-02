"""Isolated source-bound distributor/radial-plate/collar CAD study, not live edits.

Replays an explicitly retained approved cold baseline into a NEW isolated root.
Uses the normal managed component HTTP save/build/inspection/download flow.
No owner application root is opened, migrated, overwritten or restarted.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from http.cookiejar import CookieJar
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from api.project_authority import principal
from gui.server import CosmosApplication, CosmosApplicationHandler
from systems.geometry.component_authority import injector_dimensions
from systems.geometry.component_model import IDENTITY
from systems.projects.authority import Head
from systems.projects.models import PropulsionDesign


def proposed_model(source,old_spec,parameters):
    if parameters["schema"]!="cosmos.proposed-interface-layout.v1" or parameters["scope"]!="PROVISIONAL_ISOLATED_GEOMETRY_STUDY_NOT_APPROVED_ENGINE_INPUTS":
        raise ValueError("Explicit labelled geometry hypotheses required, not accepted engine inputs")
    if {f["operation"] for f in old_spec["features"]}!={"profile.wall","cooling.axial_sector","injector.biprop_doublet"}:
        raise ValueError("Use the exact retained preceding assembly, not arbitrary component geometry")
    q=lambda v,u="m":{"value":v,"unit":u}
    spec=deepcopy(old_spec);old_plate=next(f for f in spec["features"] if f["operation"]=="injector.biprop_doublet")
    spec["features"]=[f for f in spec["features"] if f is not old_plate]
    spec["frames"]=[f for f in spec["frames"] if f["id"]!=old_plate["frame"]]
    spec["outputs"]=[v for v in spec["outputs"] if v!=old_plate["id"]]
    spec["source"]=parameters["source"]
    profile=next(f for f in spec["features"] if f["operation"]=="profile.wall")["parameters"]
    start=profile["x0"]["value"]
    plate=deepcopy(old_plate);plate["id"]="radial-injector";plate["operation"]="injector.biprop_radial_doublet";plate["frame"]="radial-plate-frame"
    dims,_=injector_dimensions(source)
    plate["parameters"].update(deepcopy(dims));plate["parameters"]["separation"]=q(parameters["pair_separation_m"])
    headers=parameters.get("cooling_headers")
    if headers:
        if parameters.get("injector_enclosure_radius_basis")!="EXACT_CHAMBER_GAS_BORE":raise ValueError("Header study requires an explicit alternative enclosure radius basis")
        plate["parameters"]["radius"]=deepcopy(profile["inner0"])
    plate_start=start-plate["parameters"]["thickness"]["value"]-parameters["injector_to_chamber_gap_m"]
    head=parameters["head"]
    h={key[:-2]:q(value) for key,value in head.items() if key.endswith("_m")}
    h.update({key[:-4]:q(value,"rad") for key,value in head.items() if key.endswith("_rad")})
    h["radius"]=deepcopy(plate["parameters"]["radius"])
    for key in ("ring_radius","separation","count","fuel_hole_radius","oxidizer_hole_radius","phase"):
        h[key]=deepcopy(plate["parameters"][key])
    length=sum(head[k] for k in ("back_web_m","plenum_length_m","front_web_m"))
    def frame(name,x):
        spec["frames"].append({"id":name,"parent":"world","origin":[q(x),q(0.),q(0.)],"rotation":list(IDENTITY)})
    frame("radial-plate-frame",plate_start);frame("head-frame",plate_start-length)
    spec["features"].extend([{"id":"isolated-dual-manifold","operation":"manifold.dual_annular","frame":"head-frame","depends_on":[],"parameters":h},plate])
    spec["outputs"].extend(["isolated-dual-manifold","radial-injector"])
    collar=parameters["mounting_collar"]
    cp={key[:-2]:q(value) for key,value in collar.items() if key.endswith("_m")}
    cp.update(bore_radius=deepcopy(profile["outer0"]),count=q(collar["count"],"1"),phase=q(collar["phase_rad"],"rad"))
    if not headers and plate["parameters"]["radius"]!=cp["bore_radius"]:raise ValueError("This explicit collar proposal needs matching retained plate/body outer radii; no automatic change")
    collars=(("chamber-collar",start),) if headers else (("chamber-collar",start),("plate-collar",start-collar["thickness_m"]))
    for name,x in collars:
        frame(name+"-frame",x)
        spec["features"].append({"id":name,"operation":"interface.bolted_flange","frame":name+"-frame","depends_on":[],"parameters":deepcopy(cp)})
        spec["outputs"].append(name)
    if headers:
        channel=next(f for f in spec["features"] if f["operation"]=="cooling.axial_sector")["parameters"]
        for name,index,rotation in (("upper",0,list(IDENTITY)),("lower",int(profile["point_count"]["value"])-1,[-1.,0.,0.,0.,1.,0.,0.,0.,-1.])):
            config=headers[name];radius=profile["inner"+str(index)]["value"];x=profile["x"+str(index)]["value"]
            low=radius+channel["hot_ligament"]["value"];high=low+channel["depth"]["value"]
            hp={key[:-2]:q(value) for key,value in config.items() if key.endswith("_m")}
            length=sum(config[key] for key in ("back_web_m","plenum_length_m","front_web_m"))
            hp.update(bore_radius=q(radius),outer_radius=q(collar["outer_radius_m"] if name=="upper" else high+headers["plenum_outer_clearance_m"]+headers["lower_roof_thickness_m"]),
                plenum_inner=q(low-headers["plenum_inner_clearance_m"]),plenum_outer=q(high+headers["plenum_outer_clearance_m"]),
                port_inner=q(low),port_outer=q(high),supply_hole_radius=q(headers["supply_hole_radius_m"]),supply_phase=q(headers["supply_phase_rad"],"rad"),
                count=deepcopy(channel["count"]),width=deepcopy(channel["width"]),
                phase=q(channel["phase"]["value"] if name=="upper" else -channel["phase"]["value"]-channel["width"]["value"],"rad"))
            fid=name+"-coolant-header"
            spec["frames"].append({"id":fid,"parent":"world","origin":[q(x-length if name=="upper" else x+length),q(0.),q(0.)],"rotation":rotation})
            spec["features"].append({"id":fid,"operation":"manifold.cooling_annular","frame":fid,"depends_on":[],"parameters":hp});spec["outputs"].append(fid)
    return spec


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assembly",type=Path,required=True);p.add_argument("--parameters",type=Path,required=True)
    p.add_argument("--runtime",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--port",type=int,required=True);p.add_argument("--serve",action="store_true")
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False,mode=0o700)
    baseline_raw=(args.assembly/"engine-baseline.json").read_bytes()
    old_raw=(args.assembly/"component-specification.json").read_bytes();params_raw=args.parameters.read_bytes()
    baseline=json.loads(baseline_raw);d=PropulsionDesign.from_canonical_dict(json.loads(baseline["source_canonical_json"]))
    if "approved cold study" not in d.name:raise ValueError("Use the separately labelled approved study, not an unapproved owner case")
    parameters=json.loads(params_raw);spec=proposed_model(d,json.loads(old_raw),parameters)
    def save(name,value):
        (out/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n")
    save("proposed-inputs.json",parameters);save("proposed-component-specification.json",spec)
    save("source-replay.json",{"source_authority":baseline["authority"],"baseline_file_sha256":sha256(baseline_raw).hexdigest(),
        "component_file_sha256":sha256(old_raw).hexdigest(),"parameters_sha256":sha256(params_raw).hexdigest(),
        "scope":"EXPLICIT_COLD_SOURCE_REPLAY_IN_NEW_ISOLATED_PROJECT_NOT_LIVE_OWNER_AUTHORITY"})
    app=CosmosApplication(out/"app-data",new_shell=True,ngg_enabled=True,ngg_runtime=args.runtime.resolve(),durable_projects=True)
    class Handler(CosmosApplicationHandler):
        application=app
        def log_message(self,*_args):pass
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base="http://127.0.0.1:"+str(server.server_port)
    client=build_opener(HTTPCookieProcessor(CookieJar()))
    def request(path,data=None,*,binary=False):
        raw=None if data is None else json.dumps(data,allow_nan=False).encode()
        with client.open(Request(base+path,data=raw,headers={"Content-Type":"application/json"}),timeout=120) as response:
            value=response.read() if binary else json.load(response)
        if not binary and value.get("ok") is False:raise ValueError(value.get("error"))
        return value
    try:
        request("/api/auth/login",{"login_id":"cosmos-admin","password":"COSMOS-Dev-2026!","login_profile":"ADMIN"})
        project=request("/api/projects",{"title":"ISOLATED 1.5kN distributor/interfaces study - NOT complete engine","mission":"Preliminary software geometry study, not hardware approval","operation_id":str(uuid4())})["project"]
        # Explicit source replay through existing authority, not a claimed new
        # thermochemical/operating solve or a raw database write.
        source=app.project_api.service.create(principal(app.auth.list_users()[0]),project["project_id"],design=d,operation_id="retained-cold-source-replay",command_hash=sha256(baseline_raw).hexdigest())
        root="/api/projects/"+project["project_id"]
        model=request(root+"/component-geometry",{"title":"Proposed radial injector + isolated dual manifold + collars - seal/pipe/thermal pending",
            "baseline_commit_id":source.commit_id,"expected_baseline":asdict(source.head),"specification":spec,"expected":asdict(Head.absent()),"operation_id":str(uuid4())})
        save("model-envelope.json",model)
        interfaces=request(root+"/component-interfaces/"+model["authority"]["object_id"]+"?commit="+model["authority"]["commit_id"]+"&tolerance_m="+str(parameters["numerical_interface_tolerance_m"]))
        save("interface-inspection.json",interfaces)
        expected_pairs=next(f for f in spec["features"] if f["operation"]=="manifold.dual_annular")["parameters"]["count"]["value"]
        expected_headers=2*next(f for f in spec["features"] if f["operation"]=="cooling.axial_sector")["parameters"]["count"]["value"] if parameters.get("cooling_headers") else 0
        if len(interfaces["matches"])!=2*expected_pairs+expected_headers:
            raise ValueError("Inspect distributor/plate geometry mismatch before any native build")
        q=lambda v,u="m":{"value":v,"unit":u}
        qa={"relative_volume":q(.01,"1"),"centroid":q(.0003),"implicit_residual":q(.0003),"reverse_distance":q(.0003),"semantic_relative_area":q(.001,"1"),"semantic_centroid":q(1e-5),
            "source":"Predeclared independent SOFTWARE QA for unreviewed interface geometry; not manufacturing tolerances, leakage or physical qualification"}
        job=request(root+"/component-geometry-builds",{"model_commit_id":model["authority"]["commit_id"],"expected_model":model["authority"]["head"],"qa_specification":qa,"output_formats":["step","stl"],"operation_id":str(uuid4())})
        uri=root+"/component-geometry-builds/"+job["object_id"]+"/jobs/"+job["job_id"]
        ids={"project_id":project["project_id"],"design_id":source.object_id,"baseline_commit_id":source.commit_id,"model_id":model["authority"]["object_id"],"model_commit_id":model["authority"]["commit_id"],"job_id":job["job_id"],"build_id":job["object_id"],
             "viewer_url":base+"/app/workbench/native-geometry?project="+project["project_id"]}
        save("identities.json",ids);print(json.dumps({"isolated_build_started":ids}),flush=True)
        deadline=time.monotonic()+420
        while job["state"] not in {"COMPLETED","FAILED","CANCELLED","INTERRUPTED"}:
            if time.monotonic()>deadline:raise TimeoutError("Retained isolated native job pending; inspect identities.json")
            time.sleep(.5);job=request(uri)
        save("native-job.json",job)
        if job["state"]!="COMPLETED" or not job["current_generated_candidate"]:raise ValueError("Isolated native software QA did not accept a current candidate; diagnostics retained")
        for name in ("source.brep","export.step","export.stl"):
            (out/("PRELIMINARY-INTERFACE-STUDY-"+name)).write_bytes(request(uri+"/blobs/"+name,binary=True))
        save("review-context.json",request(uri+"/review-context"))
        save("artifact-sha256.json",{f.name:sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()})
        coolant_matches=sum(m["opening"]=="MATCHING_WORLD_ANNULAR_SECTORS" for m in interfaces["matches"])
        print(json.dumps({"state":job["state"],"injector_distributor_connections":len(interfaces["matches"])-coolant_matches,
            "cooling_header_connections":coolant_matches,"engine_route_complete":False,"physical_validation":"NOT_PERFORMED",**ids}),flush=True)
        if args.serve:input("Isolated candidate viewer retained. Press Enter to close gracefully.\n")
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);app.close()


if __name__=="__main__":main()
