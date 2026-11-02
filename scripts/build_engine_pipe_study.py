"""Retain a NEW isolated source-replay pipe candidate through normal managed HTTP.

This is explicit cold baseline replay, not a new CEA/thermal/operating solve.
No owner root is opened, migrated, overwritten or restarted.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import asdict
from hashlib import sha256
from http.cookiejar import CookieJar
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from api.project_authority import principal
from gui.server import CosmosApplication, CosmosApplicationHandler
from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import compile_model
from systems.geometry.joint_layout import append_header_bolts
from systems.geometry.pipe_routes import append_engine_pipes
from systems.geometry.separable_head_cad import prepare_cad
from systems.projects.authority import Head
from systems.projects.models import PropulsionDesign


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("assembly","proposal","runtime","output"):parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--study",choices=("pipes","header-bolts","separable-head"),default="pipes")
    parser.add_argument("--cad-proposal",type=Path);parser.add_argument("--prepare-only",action="store_true")
    parser.add_argument("--port",type=int,default=0);parser.add_argument("--serve",action="store_true")
    args=parser.parse_args()
    if args.study=="separable-head" and args.cad_proposal is None:parser.error("--cad-proposal required for the explicit revised concept")
    out=args.output.resolve();out.mkdir(parents=True,mode=0o700,exist_ok=False)
    raw=(args.assembly/"model-envelope.json").read_bytes();old=json.loads(raw)
    baseline=json.loads(old["model"]["baseline_canonical_json"])
    design=PropulsionDesign.from_canonical_dict(baseline)
    if "approved cold study" not in design.name:raise ValueError("Explicit retained approved cold-study replay required")
    spec=old["model"]["specification"]
    value=compile_model(spec,"engine-component-retained-pipe-preparation","retained-cold-replay","2026-10-21T00:00:00+00:00")
    before=inspect_interfaces(value,1e-6)
    proposal_raw=args.proposal.read_bytes();proposal=json.loads(proposal_raw)
    if args.study=="pipes":
        spec,bindings=append_engine_pipes(spec,before,proposal)
    elif args.study=="header-bolts":
        spec=append_header_bolts(spec,before,proposal)
        bindings=json.loads((args.assembly/"route-bindings.json").read_bytes())
    else:
        cad=json.loads(args.cad_proposal.read_bytes())
        spec,bindings,layout=prepare_cad(spec,before,proposal,cad)
    def save(name,value):
        with (out/name).open("x") as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")
    save("proposal.json",proposal);save("component-specification.json",spec);save("route-bindings.json",bindings)
    if args.study=="separable-head":save("cad-proposal.json",cad);save("layout-preparation.json",layout)
    repository=Path(__file__).resolve().parents[1]
    save("preparation-identities.json",{"runtime_manifest_sha256":sha256(args.runtime.read_bytes()).hexdigest(),
        "methods":{name:sha256((repository/name).read_bytes()).hexdigest() for name in
            ("scripts/build_engine_pipe_study.py","systems/geometry/pipe_routes.py","systems/geometry/joint_layout.py","systems/geometry/component_joints.py","systems/geometry/component_circuits.py","systems/geometry/separable_head_cad.py","systems/geometry/separable_head_layout.py")}})
    save("source-replay.json",{"scope":"EXPLICIT_COLD_BASELINE_REPLAY_NOT_FRESH_ENGINE_SOLVE_OR_LIVE_OWNER_AUTHORITY",
        "retained_model_authority":old["authority"],"model_envelope_sha256":sha256(raw).hexdigest(),
        "baseline_canonical_sha256":sha256(old["model"]["baseline_canonical_json"].encode()).hexdigest(),"proposal_sha256":sha256(proposal_raw).hexdigest()})
    if args.prepare_only:
        print(json.dumps({"scope":"UNBUILT_ISOLATED_PREPARATION_ONLY","features":len(spec["features"]),"output":str(out)}));return
    app=CosmosApplication(out/"app-data",new_shell=True,ngg_enabled=True,ngg_runtime=args.runtime.resolve(),durable_projects=True)
    class Handler(CosmosApplicationHandler):
        application=app
        def log_message(self,*_args):pass
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base="http://127.0.0.1:"+str(server.server_port);client=build_opener(HTTPCookieProcessor(CookieJar()))
    def request(path,data=None,*,binary=False):
        encoded=None if data is None else json.dumps(data,allow_nan=False).encode()
        with client.open(Request(base+path,data=encoded,headers={"Content-Type":"application/json"}),timeout=120) as response:
            result=response.read() if binary else json.load(response)
        if not binary and result.get("ok") is False:raise ValueError(result.get("error"))
        return result
    try:
        request("/api/auth/login",{"login_id":"cosmos-admin","password":"COSMOS-Dev-2026!","login_profile":"ADMIN"})
        project=request("/api/projects",{"title":"ISOLATED methalox "+args.study+" - NOT complete engine","mission":"Source-bound geometry and circuit topology study only","operation_id":str(uuid4())})["project"]
        source=app.project_api.service.create(principal(app.auth.list_users()[0]),project["project_id"],design=design,
            operation_id="retained-cold-baseline-replay",command_hash=sha256(raw).hexdigest())
        root="/api/projects/"+project["project_id"]
        model=request(root+"/component-geometry",{"title":"Provisional connected engine "+args.study+"; joints, seals and hot flow pending",
            "baseline_commit_id":source.commit_id,"expected_baseline":asdict(source.head),"specification":spec,
            "expected":asdict(Head.absent()),"operation_id":str(uuid4())})
        save("model-envelope.json",model)
        inspection=request(root+"/component-interfaces/"+model["authority"]["object_id"]+"?"+urlencode({
            "commit":model["authority"]["commit_id"],"tolerance_m":1e-6,**bindings}))
        save("interface-inspection.json",inspection)
        if not inspection["circuits"]["topology_complete"]:raise ValueError("Actual source-bound circuit topology incomplete; inspect retained evidence before native generation")
        if args.study=="header-bolts":
            contacts=[c for j in inspection["mechanical_joints"]["header_joints"] if j["header_part_id"]==proposal["feature_id"]
                for c in j["contacts"] if c["part_id"]==proposal["collar_part_id"]]
            if len(contacts)!=1 or not contacts[0]["bolt_axes_complete"]:raise ValueError("Matching source collar/header bolt axes not complete; no native candidate requested")
        if args.study=="separable-head":
            contacts=inspection["mechanical_joints"]["mounting_stack_contacts"]
            if len(contacts)!=2 or not all(c["bolt_axes_complete"] for c in contacts):raise ValueError("Revised mounting stack not geometrically matched")
            if inspection["injector_discharge_to_chamber"]!="GEOMETRY_ALIGNED_APERTURES_ONLY":raise ValueError("Revised injector/gas-entry geometry not connected")
        save("pipe-flow-applicability.json",{"model_authority":model["authority"],"pipe_geometry":[{
            "part_id":p["part_id"],"centerline_length_m":p["centerline_length_m"],"bore_diameter_m":2*p["bore_radius_m"],
            "length_over_diameter":p["centerline_length_m"]/(2*p["bore_radius_m"]),
            "existing_straight_cell_geometry_domain":p["bend_radius_m"] is None and p["centerline_length_m"]>=20*p["bore_radius_m"],
            "bend_loss":"NOT_CALCULATED","minor_losses":"NOT_CALCULATED"} for p in inspection["pipe_paths"]],
            "scope":"Geometric compatibility only. Existing straight-cell L/D>=10 does not establish fluid/regime/heat/loss applicability. Curved and short pieces require appropriate models; no silent fully-developed mapping or pressure rating."})
        q=lambda v,u="m":{"value":v,"unit":u}
        qa={"relative_volume":q(.01,"1"),"centroid":q(.0003),"implicit_residual":q(.0003),"reverse_distance":q(.0003),
            "semantic_relative_area":q(.001,"1"),"semantic_centroid":q(1e-5),
            "source":"Predeclared software-only QA, same actual-engine-candidate limits as prior header study; not manufacturing tolerances"}
        job=request(root+"/component-geometry-builds",{"model_commit_id":model["authority"]["commit_id"],"expected_model":model["authority"]["head"],
            "qa_specification":qa,"output_formats":["step","stl"],"operation_id":str(uuid4())})
        uri=root+"/component-geometry-builds/"+job["object_id"]+"/jobs/"+job["job_id"]
        identities={"project_id":project["project_id"],"model_id":model["authority"]["object_id"],"model_commit_id":model["authority"]["commit_id"],
            "baseline_commit_id":source.commit_id,"job_id":job["job_id"],"build_id":job["object_id"],"viewer_url":base+"/app/workbench/native-geometry?project="+project["project_id"]}
        save("identities.json",identities);print(json.dumps({"isolated_build_started":identities}),flush=True)
        deadline=time.monotonic()+420
        while job["state"] not in {"COMPLETED","FAILED","CANCELLED","INTERRUPTED"}:
            if time.monotonic()>deadline:raise TimeoutError("Retained native candidate still pending; inspect identities.json")
            time.sleep(.5);job=request(uri)
        save("native-job.json",job)
        if job["state"]!="COMPLETED" or not job["current_generated_candidate"]:raise ValueError("Native candidate not accepted; failures retained without tolerance widening")
        prefix="PRELIMINARY-CONNECTED-"+{"pipes":"PIPES","header-bolts":"HEADER-BOLTS","separable-head":"SEPARABLE-HEAD"}[args.study]+"-"
        for name in ("source.brep","export.step","export.stl"):
            with (out/(prefix+name)).open("xb") as stream:stream.write(request(uri+"/blobs/"+name,binary=True))
        save("review-context.json",request(uri+"/review-context"))
        save("artifact-sha256.json",{p.name:sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
        print(json.dumps({"state":job["state"],"geometric_circuits_complete":True,"engine_complete":False,
            "physical_validation":"NOT_PERFORMED",**identities}),flush=True)
        if args.serve:input("Task-owned isolated pipe viewer ready. Enter closes this process gracefully.\n")
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);app.close()


if __name__=="__main__":main()
