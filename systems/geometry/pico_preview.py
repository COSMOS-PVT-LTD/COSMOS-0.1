"""Bounded, topology-checked display LOD. Originals and engineering QA stay intact."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import numpy as np

from infrastructure.geometry import WorkerCommand
from systems.contracts.geometry._wire import require
from systems.geometry.component_reference import PartReference
from systems.geometry.pico_mesh_qa import audit_part
from systems.geometry.qa import STL_RECORD


def reduce_preview(workspace,raw,parts,plan,limits,*,cancellation=None,check_budget=lambda:None):
    check_budget();cfg=workspace.configuration();digest=sha256(raw);digest.update(json.dumps(parts,sort_keys=True).encode());digest.update(repr(limits).encode());digest.update(cfg["manifest_sha256"].encode());key=digest.hexdigest()
    with workspace.preview_lock:
        if key in workspace.previews:return workspace.previews[key]
        command=cfg.get("preview_worker")
        require(command is not None,"PICO_PREVIEW_RUNTIME","Large mesh display requires a separately pinned topology-preserving preview worker")
        with tempfile.TemporaryDirectory(prefix="display-",dir=workspace.root) as folder:
            directory=Path(folder)
            with (directory/"input.stl").open("xb") as f:f.write(raw)
            payload=json.dumps({"parts":parts,"sha256":sha256(raw).hexdigest()},allow_nan=False).encode()
            process=workspace.supervisor.submit("display-"+key[:32],WorkerCommand(tuple(command["argv"]),tuple(command["environment"].items())),payload,directory,cancellation=cancellation).result(timeout=310)
            require(process.code=="OK" and process.exit_code==0,"PICO_PREVIEW_REDUCTION",
                "Display reduction failed: code="+process.code+" exit="+str(process.exit_code)+" observed_rss="+str(process.maximum_rss_bytes)+" stderr="+process.stderr.decode("utf-8",errors="replace")[-1500:]+"; originals unchanged")
            meta=json.loads(process.stdout);path=directory/"positions.f32"
            require(path.is_file() and not path.is_symlink() and 0<path.stat().st_size<=7200000,"PICO_PREVIEW","Bounded display-only vertices required")
            data=path.read_bytes();require(len(data)%36==0 and sha256(data).hexdigest()==meta["sha256"],"PICO_PREVIEW","Display integrity mismatch")
            triangles=np.frombuffer(data,dtype="<f4").reshape(-1,3,3);records=np.zeros(len(triangles),dtype=STL_RECORD);records["vertices"]=triangles
            normals=np.cross(triangles[:,1].astype(float)-triangles[:,0],triangles[:,2].astype(float)-triangles[:,0]);lengths=np.linalg.norm(normals,axis=1)
            require(np.isfinite(triangles).all() and (lengths>0).all(),"PICO_PREVIEW","Nonfinite/degenerate display triangles rejected")
            records["normal"]=normals/lengths[:,None];checks=[];start=0
            require(len(meta["parts"])==len(plan.parts),"PICO_PREVIEW","Missing display parts")
            for source,part,actual in zip(parts,plan.parts,meta["parts"],strict=True):
                require(all(actual.get(k)==source[k] for k in ("part_id","feature_id","frame_id","role")) and actual["part_id"]==part.part_id and actual["triangle_start"]==start and type(actual["triangle_count"]) is int and actual["triangle_count"]>0 and actual["source_triangle_start"]==source["triangle_start"] and actual["source_triangle_count"]==source["triangle_count"],"PICO_PREVIEW","Display part/source ranges changed")
                stop=start+actual["triangle_count"];checks.append(audit_part(records[start:stop],PartReference(plan,part),limits,check_budget));start=stop
            require(start==len(records) and all(p["pass"] for p in checks),"PICO_PREVIEW_QA","Reduced display mesh failed independent topology/dimensional study checks; no hole-producing sampling fallback")
            result=(data,meta["parts"],True,{"method":meta["method"],"source_sha256":sha256(raw).hexdigest(),"preview_sha256":meta["sha256"],"parts":checks,
                "process":{"code":process.code,"exit_code":process.exit_code,"elapsed_s":process.elapsed_s,"observed_rss_bytes":process.maximum_rss_bytes},
                "physical_validation":"NOT_PERFORMED","scope":"Display-only reduction; evaluated against captured software criteria, not a new engineering artifact or certified simplification error bound"})
        if len(workspace.previews)>=4:workspace.previews.pop(next(iter(workspace.previews)))
        workspace.previews[key]=result;return result
