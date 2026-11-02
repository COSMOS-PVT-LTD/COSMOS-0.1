"""Generate source-bound CAD inspection/drawing evidence on an isolated root."""
import argparse
import json
from pathlib import Path

from api.project_authority import principal
from gui.server import CosmosApplication


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("root","runtime","output"):p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--project",required=True);p.add_argument("--job",required=True);p.add_argument("--part",required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[1];data=a.root.resolve();out=a.output.resolve()
    if repo/"output" not in data.parents or repo/"output" not in out.parents:raise ValueError("Explicit task output roots only; owner data never opened")
    out.mkdir(parents=True,exist_ok=False)
    app=CosmosApplication(data,new_shell=True,durable_projects=True,ngg_enabled=False)
    try:
        actor=principal(app.auth.list_users()[0]);service=app.project_api.cad_tools;service.path=a.runtime.resolve()
        result=service.clearance(actor,a.project,a.job,{"a":"fuel-supply","b":"oxidizer-supply","required_clearance_m":"0.001","linear_tolerance_m":"1e-8","volume_resolution_m3":"1e-15"})
        with (out/"retained-engine-clearance.json").open("x") as f:json.dump(result,f,indent=2)
        declarations={"part_id":a.part,"title":"COSMOS retained flange - source-bound CAD study","number":"COSMOS-CAD-STUDY-001","revision":"DRAFT-A","author":"COSMOS software verification","material":"NOT SPECIFIED - RESEARCH ONLY","process":"NOT SPECIFIED - RESEARCH ONLY","tolerance_note":"NOT SPECIFIED - NOT A MANUFACTURING RELEASE","finish_note":"NOT SPECIFIED","scale_denominator":"3","curve_deflection_m":"0.00001"}
        for format in ("pdf","svg"):
            evidence,content=service.drawing(actor,a.project,a.job,declarations,format)
            with (out/("UNRELEASED-flange-drawing."+format)).open("xb") as f:f.write(content)
            with (out/("drawing-"+format+"-provenance.json")).open("x") as f:json.dump(evidence,f,indent=2)
        print("Created isolated source-bound clearance and unreleased PDF/SVG:",out)
    finally:app.close()


if __name__=="__main__":main()
