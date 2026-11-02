"""Isolated source-bound native union feasibility, never accepted/published CAD.

Reads hash-verified retained B-rep and probes only collector/cooled-wall metal
continuity and source coolant void connectivity. No fuzzy fuse, fill/heal,
manufacturing process selection, owner store or viewer mutation.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from hashlib import sha256
from pathlib import Path

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import from_contracts
from systems.geometry.integral_collector_study import prepare_probe


def native(output):
    import OCP  # type: ignore[import-not-found]
    from OCP.BRep import BRep_Builder  # type: ignore[import-not-found]
    from OCP.BRepAdaptor import BRepAdaptor_Surface  # type: ignore[import-not-found]
    from OCP.BRepAlgoAPI import (  # type: ignore[import-not-found]
        BRepAlgoAPI_Common,
        BRepAlgoAPI_Fuse,
    )
    from OCP.BRepBuilderAPI import (  # type: ignore[import-not-found]
        BRepBuilderAPI_MakeEdge,
        BRepBuilderAPI_MakeFace,
        BRepBuilderAPI_MakeWire,
        BRepBuilderAPI_Transform,
    )
    from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore[import-not-found]
    from OCP.BRepGProp import BRepGProp  # type: ignore[import-not-found]
    from OCP.BRepPrimAPI import (  # type: ignore[import-not-found]
        BRepPrimAPI_MakeCylinder,
        BRepPrimAPI_MakeRevol,
    )
    from OCP.BRepTools import BRepTools  # type: ignore[import-not-found]
    from OCP.GeomAbs import GeomAbs_Plane  # type: ignore[import-not-found]
    from OCP.gp import (  # type: ignore[import-not-found]
        gp_Ax1,
        gp_Ax2,
        gp_Dir,
        gp_Pnt,
        gp_Trsf,
    )
    from OCP.GProp import GProp_GProps  # type: ignore[import-not-found]
    from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID  # type: ignore[import-not-found]
    from OCP.TopExp import TopExp_Explorer  # type: ignore[import-not-found]
    from OCP.TopoDS import (  # type: ignore[import-not-found]
        TopoDS,
        TopoDS_Iterator,
        TopoDS_Shape,
    )
    from OCP.TopTools import TopTools_ListOfShape  # type: ignore[import-not-found]

    if OCP.__version__!="7.8.1.1":raise ValueError("Pinned OCP7.8.1.1 required")
    request=json.loads(sys.stdin.buffer.read(2*1024*1024+1));probe=request["probe"]
    source=Path(request["brep"])
    if source.stat().st_size>64*1024*1024 or sha256(source.read_bytes()).hexdigest()!=request["brep_sha256"]:
        raise ValueError("Retained source B-rep identity/size mismatch")
    shape=TopoDS_Shape()
    if not BRepTools.Read_s(shape,str(source),BRep_Builder()):raise ValueError("Retained B-rep read failed")
    iterator=TopoDS_Iterator(shape);bodies=[]
    while iterator.More():bodies.append(iterator.Value());iterator.Next()
    if len(bodies)!=len(request["part_ids"]):raise ValueError("Source direct-child identity count mismatch")
    lookup=dict(zip(request["part_ids"],bodies,strict=True))
    def props(body,surface=False):
        p=GProp_GProps()
        if surface:BRepGProp.SurfaceProperties_s(body,p)
        else:BRepGProp.VolumeProperties_s(body,p)
        factor=1e-6 if surface else 1e-9
        return p.Mass()*factor,[p.CentreOfMass().X()*.001,p.CentreOfMass().Y()*.001,p.CentreOfMass().Z()*.001]
    def solids(body):
        e=TopExp_Explorer(body,TopAbs_SOLID);count=0
        while e.More():count+=1;e.Next()
        return count
    def operation(kind,a,b):
        op=kind();arguments=TopTools_ListOfShape();arguments.Append(a);tools=TopTools_ListOfShape();tools.Append(b)
        op.SetArguments(arguments);op.SetTools(tools);op.SetNonDestructive(True);op.SetRunParallel(False);op.SetFuzzyValue(0.);op.Build()
        if not op.IsDone():raise ValueError("Exact native Boolean failed; no healing/fuzzy retry")
        result=op.Shape()
        if not BRepCheck_Analyzer(result,True).IsValid():raise ValueError("Native result invalid; no partial acceptance")
        return result
    for record in probe["expected_parts"]:
        body=lookup[record["part_id"]];v,c=props(body)
        if solids(body)!=1 or not math.isclose(v,record["volume_m3"],rel_tol=1e-8) or max(abs(a-b) for a,b in zip(c,record["centroid_m"],strict=True))>1e-9:
            raise ValueError("Native source part must independently match selected analytic identity")
    header,wall=[lookup[probe[k]] for k in ("collector_id","chamber_id")]
    common=operation(BRepAlgoAPI_Common,header,wall);overlap,_=props(common)
    def contact_faces(body):
        faces=[];e=TopExp_Explorer(body,TopAbs_FACE)
        while e.More():
            face=TopoDS.Face_s(e.Current());surface=BRepAdaptor_Surface(face)
            if surface.GetType()==GeomAbs_Plane:
                plane=surface.Plane()
                if abs(abs(plane.Axis().Direction().X())-1)<1e-12 and abs(plane.Location().X()*.001-probe["contact_x_m"])<=1e-12:
                    faces.append(face)
            e.Next()
        if not faces:raise ValueError("Exact native source contact plane missing")
        return faces
    # A volume-dimensional Common of merely touching solids is empty in OCCT.
    # Measure the actual coincident trimmed faces; do not weaken the area test.
    contact=math.fsum(props(operation(BRepAlgoAPI_Common,a,b),True)[0] for a in contact_faces(header) for b in contact_faces(wall))
    fused=operation(BRepAlgoAPI_Fuse,header,wall);metal_volume,_=props(fused)
    def revolve(profile,sector):
        points=[(x,ri) for x,ri,_ in profile]+[(x,ro) for x,_,ro in reversed(profile)]
        wire=BRepBuilderAPI_MakeWire()
        for a,b in zip(points,points[1:]+points[:1],strict=True):wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(a[0]*1000,a[1]*1000,0),gp_Pnt(b[0]*1000,b[1]*1000,0)).Edge())
        face=BRepBuilderAPI_MakeFace(wire.Wire(),True)
        rev=BRepPrimAPI_MakeRevol(face.Face(),gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),sector[1],True) if sector else BRepPrimAPI_MakeRevol(face.Face(),gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),True)
        if not face.IsDone() or not rev.IsDone():raise ValueError("Exact source coolant-void revolution failed")
        result=rev.Shape()
        if sector:
            tr=gp_Trsf();tr.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),sector[0]);mover=BRepBuilderAPI_Transform(result,tr,True)
            if not mover.IsDone():raise ValueError("Coolant sector rigid placement failed")
            result=mover.Shape()
        return result
    fluid=None
    for item in probe["fluid_profiles"]:
        piece=revolve(item["profile"],item["sector"])
        fluid=piece if fluid is None else operation(BRepAlgoAPI_Fuse,fluid,piece)
    for hole in probe["fluid_holes"]:
        cylinder=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*[v*1000 for v in hole["origin"]]),gp_Dir(1,0,0)),hole["radius"]*1000,hole["length"]*1000).Shape()
        fluid=operation(BRepAlgoAPI_Fuse,fluid,cylinder)
    if fluid is None:raise ValueError("Explicit source coolant cavities required")
    fluid_volume,_=props(fluid);blocked=operation(BRepAlgoAPI_Common,fused,fluid);blocked_volume,_=props(blocked)
    conditions={"single_metal_solid":solids(fused)==1,"single_connected_coolant_void":solids(fluid)==1,
        "source_contact_area":math.isclose(contact,probe["expected_contact_area_m2"],rel_tol=1e-8),
        "no_source_solid_volume_overlap":abs(overlap)<1e-12,
        "metal_volume_conserved":math.isclose(metal_volume,probe["expected_fused_metal_volume_m3"],rel_tol=1e-8),
        "coolant_volume_conserved":math.isclose(fluid_volume,probe["expected_connected_fluid_volume_m3"],rel_tol=1e-8),
        "no_solid_blocking_source_coolant":abs(blocked_volume)<1e-12}
    result={"scope":probe["scope"],"checks":conditions,"all_diagnostic_checks_pass":all(conditions.values()),
        "metal_solids":solids(fused),"coolant_void_solids":solids(fluid),"contact_area_m2":contact,
        "metal_volume_m3":metal_volume,"coolant_volume_m3":fluid_volume,"blocked_coolant_volume_m3":blocked_volume,
        "source_graph_id":probe["source_graph_id"],"component_admission":"NOT_PERFORMED","step_stl_qualification":"NOT_PERFORMED",
        "material_partition":probe["material_partition"],"manufacturing_acceptance":"NOT_PERFORMED","physical_validation":"NOT_PERFORMED"}
    if all(conditions.values()):
        for name,body in (("UNQUALIFIED-integral-metal.brep",fused),("UNQUALIFIED-connected-coolant-void.brep",fluid)):
            target=output/name
            if target.exists() or not BRepTools.Write_s(body,str(target)):raise ValueError("Refuse partial/overwritten diagnostic B-rep")
    print(json.dumps(result,allow_nan=False),flush=True)
    if not all(conditions.values()):raise SystemExit(1)


def main():
    if len(sys.argv)==3 and sys.argv[1]=="--native":native(Path(sys.argv[2]));return
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("assembly","runtime","output"):parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--collector",required=True);parser.add_argument("--chamber",required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];cfg=json.loads(args.runtime.read_bytes())
    native_hashes={name:value for name,value in cfg["sha256"].items() if not Path(name).is_relative_to(root) or name==cfg["occt"]["argv"][0]}
    if not native_hashes or any(sha256(Path(name).read_bytes()).hexdigest()!=value for name,value in native_hashes.items()):raise ValueError("Pinned native dependency changed")
    recorded=json.loads((args.assembly/"artifact-sha256.json").read_bytes())
    names=("model-envelope.json","native-job.json","component-specification.json","PRELIMINARY-CONNECTED-SEPARABLE-HEAD-source.brep")
    for name in names:
        if sha256((args.assembly/name).read_bytes()).hexdigest()!=recorded[name]:raise ValueError("Retained source bytes changed: "+name)
    envelope=json.loads((args.assembly/"model-envelope.json").read_bytes());job=json.loads((args.assembly/"native-job.json").read_bytes())
    if job["state"]!="COMPLETED" or not job["qa"]["qa-step"]["pass"] or not job["qa"]["qa-stl"]["pass"]:
        raise ValueError("Exact preceding accepted software-only CAD attempt required")
    saved=envelope["model"]
    plan=from_contracts(DesignSnapshot.from_json(saved["snapshot_json"]),GeometryFeatureGraph.from_json(saved["graph_json"]))
    retained=json.loads(json.loads(job["source_canonical_json"])["record_json"])
    if (retained["feature_graph"]["graph_id"]!=plan.graph.graph_id
        or retained["request"]["feature_graph_sha256"]!=plan.graph.content_sha256
        or retained["request"]["snapshot_id"]!=plan.snapshot.snapshot_id):
        raise ValueError("Retained native job and model must share the exact saved graph, not a recompiled rounded specification")
    probe=prepare_probe(plan,inspect_interfaces(plan,1e-6),collector_id=args.collector,chamber_id=args.chamber)
    payload={"probe":probe,"brep":str((args.assembly/names[-1]).resolve()),"brep_sha256":recorded[names[-1]],
        "part_ids":[p["part_id"] for p in job["qa"]["worker_observations"]["parts"]]}
    out=args.output.resolve();out.mkdir(parents=True,mode=0o700,exist_ok=False)
    def save(name,value):
        with (out/name).open("x") as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write("\n")
    save("source-probe.json",payload);save("provenance.json",{"source_model_authority":envelope["authority"],"source_artifacts_sha256":{n:recorded[n] for n in names},
        "methods":{n:sha256((root/n).read_bytes()).hexdigest() for n in ("scripts/probe_integral_collector.py","systems/geometry/integral_collector_study.py","systems/geometry/component_model.py","systems/geometry/component_reference.py")},
        "scope":probe["scope"],"native_dependency_hashes":native_hashes})
    command=WorkerCommand((cfg["occt"]["argv"][0],str(Path(__file__).resolve()),"--native",str(out)),tuple(cfg["occt"]["environment"].items()))
    with WorkerSupervisor(timeout_s=180) as supervisor:
        process=supervisor.submit("integral-collector-probe",command,json.dumps(payload,allow_nan=False).encode(),out).result(timeout=190)
    (out/"worker-stdout.json").write_bytes(process.stdout);(out/"worker-stderr.txt").write_bytes(process.stderr)
    save("process.json",{"code":process.code,"exit_code":process.exit_code,"elapsed_s":process.elapsed_s,"scope":probe["scope"]})
    if process.code!="OK":raise ValueError("Isolated integral probe failed; retained stdout/stderr are diagnostic only")
    result=json.loads(process.stdout);save("diagnostic-result.json",result)
    save("diagnostic-artifact-sha256.json",{p.name:sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
    print(json.dumps({k:result[k] for k in ("scope","all_diagnostic_checks_pass","metal_solids","coolant_void_solids")}))


if __name__=="__main__":main()
