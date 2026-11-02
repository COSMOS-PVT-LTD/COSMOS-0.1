"""Unqualified native smoke for explicit prepared specifications; NOT acceptance.

Allows development before a new software campaign. Uses pinned interpreter and
native dependency identities; changed application sources are deliberately not
represented as qualified. Does not open owner data or a server, publish exports
or create a software/human/physical acceptance receipt.
"""
import argparse
import json
from hashlib import sha256
from pathlib import Path

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.component_adapter import ComponentAdapter
from systems.contracts.geometry import (
    GeometryBuildRequest,
    OutputFormat,
    Representation,
)
from systems.geometry.component_model import VERSION, compile_model


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("specification","runtime","output"):parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args();cfg=json.loads(args.runtime.read_bytes());root=Path(__file__).resolve().parents[1]
    # No claim that edited source hashes match the preceding qualification.
    native={name:value for name,value in cfg["sha256"].items() if not Path(name).is_relative_to(root) or name==cfg["occt"]["argv"][0]}
    if not native or any(sha256(Path(name).read_bytes()).hexdigest()!=value for name,value in native.items()):
        raise ValueError("Pinned native dependency identity changed")
    raw=args.specification.read_bytes();plan=compile_model(json.loads(raw),"engine-component-unqualified-smoke","UNQUALIFIED","2026-10-21T00:00:00Z")
    args.output.mkdir(parents=True,mode=0o700,exist_ok=False);out=args.output.resolve()
    parameters={p.name:p.value_si for p in plan.snapshot.parameters_si}
    request=GeometryBuildRequest("unqualified-smoke",plan.snapshot.snapshot_id,plan.graph.graph_id,plan.graph.content_sha256,
        "occt",VERSION,Representation.ANALYTIC_BREP,"none",parameters["source_tolerance"],parameters["export_tolerance"],None,
        (OutputFormat.STEP,OutputFormat.STL),"world","unqualified-smoke")
    worker=WorkerCommand((cfg["occt"]["argv"][0],str(root/"plugins/geometry/workers/component_worker.py")),tuple(cfg["occt"]["environment"].items()))
    with WorkerSupervisor(timeout_s=180,stdout_limit=16*1024*1024) as supervisor:
        adapter=ComponentAdapter("occt",worker,supervisor,enabled=True)
        process=adapter.build("unqualified-smoke",request,plan.snapshot,plan.graph,out).result(timeout=190)
        (out/"worker-stdout.jsonl").write_bytes(process.stdout);(out/"worker-stderr.txt").write_bytes(process.stderr)
        summary={"scope":"UNQUALIFIED_DIAGNOSTIC_ONLY_NOT_ACCEPTED_OR_PUBLISHED","process_code":process.code,
            "specification_sha256":sha256(raw).hexdigest(),"source_graph_id":plan.graph.graph_id,
            "methods":{name:sha256((root/name).read_bytes()).hexdigest() for name in
                ("systems/geometry/component_model.py","systems/geometry/component_reference.py","plugins/geometry/workers/component_worker.py")}}
        if process.code=="OK":
            decoded=adapter.decode(process,request,out);summary["triangles"]=decoded.metrics["triangle_count"]
            summary["parts"]=[{"id":p["part_id"],"triangles":p["triangle_count"]} for p in decoded.metrics["parts"]]
        else:summary["events"]=[json.loads(line) for line in process.stdout.splitlines()]
        with (out/"diagnostic-summary.json").open("x") as stream:json.dump(summary,stream,indent=2);stream.write("\n")
        print(json.dumps({k:v for k,v in summary.items() if k!="methods"}))
        if process.code!="OK":raise SystemExit(1)


if __name__=="__main__":main()
