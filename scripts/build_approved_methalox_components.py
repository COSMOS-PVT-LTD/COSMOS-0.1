"""Append a source-bound preliminary cold-injector assembly through normal APIs.

Retains current approved-study baseline, original CAD and every native attempt.
Cooling sectors remain explicitly illustrative, NOT a solved thermal design.
No review acceptance, manifold/seal invention, migration or hardware approval.
"""
from __future__ import annotations

import argparse
import json
import time
from hashlib import sha256
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("api","project","design","source-commit","output"):
        parser.add_argument("--"+name,required=True)
    args=parser.parse_args()
    address=urlparse(args.api)
    if address.scheme!="http" or address.hostname!="127.0.0.1" or address.username or address.path not in ("","/"):
        raise ValueError("Explicit loopback local-development API required")
    out=Path(args.output).absolute();out.mkdir(parents=True,exist_ok=False,mode=0o700)
    client=build_opener(HTTPCookieProcessor(CookieJar()))
    def read(path,data=None,*,binary=False):
        encoded=None if data is None else json.dumps(data,allow_nan=False).encode()
        with client.open(Request(args.api.rstrip("/")+path,data=encoded,headers={"Content-Type":"application/json"}),timeout=120) as response:
            result=response.read() if binary else json.load(response)
        if not binary and result.get("ok") is False: raise ValueError(result.get("error"))
        return result
    def save(name,value):
        (out/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n")
    q=lambda value,unit="m":{"value":value,"unit":unit}
    read("/api/auth/login",{"login_id":"cosmos-admin","password":"COSMOS-Dev-2026!","login_profile":"ADMIN"})
    base="/api/projects/"+args.project
    source_path=base+"/designs/"+args.design
    before=read(source_path)
    if before["authority"]["commit_id"]!=args.source_commit:
        raise ValueError("Current approved-study source changed; no writes performed")
    if "approved cold study" not in before["design"]["name"]:
        raise ValueError("Use the separately labelled approved cold-study design; not the original owner case")
    save("source-before-recalculation.json",before)
    baseline=read(source_path+"/run/analysis",{"expected":before["authority"]["head"],"operation_id":str(uuid4()),"phase3_inputs":{},"phase4_inputs":{}})
    save("engine-baseline.json",baseline)
    if not baseline["execution_ok"] or baseline["stages"]["injector"]["status"]!="CURRENT":
        raise ValueError("Retained analysis needs correction; no CAD candidate requested")
    common={"source_tolerance":q(1e-6),"export_tolerance":q(.00015),
        "source":"Exact approved cold-study chamber/nozzle and hydraulic injector. Prior provisional CAD plate/layout/radial wall retained. Illustrative cooling sectors only: no solved coolant/thermal/material/joint/hardware claim."}
    chamber=read(base+"/component-geometry/seed-from-design",{"baseline_commit_id":baseline["authority"]["commit_id"],
        "settings":{**common,"wall_thickness":q(.006),"convergent_length":q(.045),"throat_land_length":q(.003)}})
    spec=chamber["specification"]
    parameters=spec["features"][0]["parameters"]
    x0,radius=parameters["x0"]["value"],parameters["inner0"]["value"]
    injector=read(base+"/component-geometry/seed-injector-from-design",{"baseline_commit_id":baseline["authority"]["commit_id"],
        "settings":{**common,"radius":q(radius+.006),"thickness":q(.008),"ring_radius":q(radius*.65),
            "separation":q(.010),"angle":q(.25,"rad"),"phase":q(0,"rad")}})
    save("injector-source-binding.json",injector)
    spec["frames"].append({"id":"injector-frame","parent":"world","origin":[q(x0-.009),q(0),q(0)],"rotation":[1,0,0,0,1,0,0,0,1]})
    injector_feature=injector["specification"]["features"][0]
    injector_feature["frame"]="injector-frame"
    spec["features"].extend([
        {"id":"illustrative-sector-cooling","operation":"cooling.axial_sector","frame":"world","depends_on":["thrust-chamber"],
         "parameters":{"count":q(6,"1"),"width":q(.14,"rad"),"hot_ligament":q(.0015),"depth":q(.0025),"phase":q(.1,"rad"),"fluid_domains":q(1,"1")}},injector_feature])
    spec["outputs"]=["illustrative-sector-cooling",injector_feature["id"]]
    save("component-specification.json",spec)
    model=read(base+"/component-geometry",{"title":"Source-bound cold injector + thrust chamber · illustrative cooling · UNREVIEWED",
        "baseline_commit_id":baseline["authority"]["commit_id"],"expected_baseline":baseline["authority"]["head"],
        "specification":spec,"expected":{"version":0,"content_hash":sha256(b"").hexdigest()},"operation_id":str(uuid4())})
    save("model-envelope.json",model)
    limits={"relative_volume":q(.01,"1"),"centroid":q(.0003),"implicit_residual":q(.0003),"reverse_distance":q(.0003),
        "semantic_relative_area":q(.001,"1"),"semantic_centroid":q(1e-5),
        "source":"Predeclared preliminary SOFTWARE QA only: 1% volume;0.30mm centroid/sampled distances;0.1% face-area and0.01mm face-centroid mapping. Not manufacturing tolerances or engineering acceptance."}
    job=read(base+"/component-geometry-builds",{"model_commit_id":model["authority"]["commit_id"],"expected_model":model["authority"]["head"],
        "qa_specification":limits,"output_formats":["step","stl"],"operation_id":str(uuid4())})
    ids={"project_id":args.project,"design_id":args.design,"baseline_commit_id":baseline["authority"]["commit_id"],
         "model_id":model["authority"]["object_id"],"model_commit_id":model["authority"]["commit_id"],"build_object_id":job["object_id"],"job_id":job["job_id"]}
    save("identities.json",ids);print(json.dumps({"native_job_started":ids}),flush=True)
    uri=base+"/component-geometry-builds/"+job["object_id"]+"/jobs/"+job["job_id"]
    deadline=time.monotonic()+420
    while job["state"] not in {"COMPLETED","FAILED","CANCELLED","INTERRUPTED"}:
        if time.monotonic()>deadline: raise TimeoutError("Retained native job is still pending; inspect identities.json")
        time.sleep(.5);job=read(uri)
    save("native-job.json",job)
    if job["state"]!="COMPLETED" or not job["current_generated_candidate"]:
        raise ValueError("Native software QA did not accept a current candidate; no CAD delivered. Retained diagnostics preserved")
    for name in ("source.brep","export.step","export.stl"):
        (out/("PRELIMINARY-UNREVIEWED-"+name)).write_bytes(read(uri+"/blobs/"+name,binary=True))
    save("review-context.json",read(uri+"/review-context"));save("software-qa.json",job["qa"])
    save("artifact-sha256.json",{p.name:sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
    print(json.dumps({"native_state":job["state"],"current_generated_candidate":True,"physical_validation":"NOT_PERFORMED",
                      "cooling":"ILLUSTRATIVE_NOT_SIZED","independent_human_review":"NOT_PERFORMED",**ids}),flush=True)


if __name__=="__main__": main()
