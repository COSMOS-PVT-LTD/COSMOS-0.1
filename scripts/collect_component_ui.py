"""Actual browser downloads vs retained originals in a task-owned synthetic root."""
import argparse
import json
from hashlib import sha256
from pathlib import Path

from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import client_for, request


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--root",type=Path,required=True);parser.add_argument("--label",choices=("before-restart","after-restart"),required=True);args=parser.parse_args()
    if not str(args.root.resolve()).startswith("/private/tmp/cosmos-r07-components-qa."): raise ValueError("Only exact task-owned synthetic root allowed")
    directory=Path(__file__).resolve().parents[1]/"docs/implementation/evidence/R07_COMPONENTS_2026-10-20"
    state=json.loads((args.root/"QA_STATE.json").read_bytes());downloads=json.loads((directory/"ui-download-map.json").read_bytes())
    base="http://127.0.0.1:8877";client=client_for(base,"component-builder","Synthetic-Component-Only!","ENGINEER")
    prefix="/api/projects/"+state["project_id"];object_id="db4e9313-d9fa-5c4a-9471-5da25fc2cced";job_id="8a422446-15a1-43f3-81f4-e0ed2a008d75";uri=prefix+"/component-geometry-builds/"+object_id+"/jobs/"+job_id
    setup_uri=prefix+"/component-studies/cb8d8bdc-4d8f-5778-b40b-5528a67929fa";review_uri=prefix+"/component-geometry-reviews/3048572c-8412-5365-9b74-1cc1802e22a3"
    job=request(client,base,uri);setup=request(client,base,setup_uri);review=request(client,base,review_uri)
    assert job["state"]=="COMPLETED" and job["current_generated_candidate"] and job["qa"]["qa-step"]["pass"] and job["qa"]["qa-stl"]["pass"]
    assert setup["upstream_current"] and review["upstream_current"]
    contract=json.loads(setup["record"]["setup_json"])
    assert contract["solver_supported"] is False and contract["execution_status"]=="NOT_STARTED" and contract["mesh_status"]=="NOT_GENERATED" and contract["physical_validation"]=="NOT_PERFORMED"
    paths={name:uri+"/blobs/"+name for name in ("source.brep","export.step","export.stl")}
    paths.update({"record.json":uri+"/record.json","inputs.json":prefix+"/component-geometry-builds/"+object_id+"/inputs.json","reviewed.step":setup_uri+"/blobs/export.step","setup.json":setup_uri+"/record.json"})
    proofs=[]
    for name,path in paths.items():
        retained=binary(client,base,path);downloaded=Path(downloads[name]).read_bytes();assert downloaded==retained,name
        proofs.append({"name":name,"bytes":len(retained),"sha256":sha256(retained).hexdigest(),"browser_download_equal":True})
    original=binary(client,base,uri+"/blobs/export.step");assert sha256(original).hexdigest()==contract["handoff"]["geometry_integrity_sha256"]
    assert binary(client,base,setup_uri+"/blobs/export.step")==original
    context=request(client,base,uri+"/review-context");section=request(client,base,uri+"/sections?part_id=feature-2&x_m=-0.2")
    model=request(client,base,prefix+"/component-geometry/fb27c313-da09-58fe-9911-501ec299571e")
    assert model["authority"]["head"]["version"]==4 and model["usable_current_model"]
    baseline=request(client,base,prefix+"/records/"+state["baseline_commit_id"])
    assert baseline["authority"]["head"]==state["baseline_head"]
    observed=job["qa"]["worker_observations"]
    result={"label":args.label,"synthetic_workflow_only_not_real_acceptance":True,"project_id":state["project_id"],"job_id":job_id,"build_object_id":object_id,"source_commit_id":job["source_commit_id"],"state":job["state"],"current_generated_candidate":job["current_generated_candidate"],"native_triangles":observed["triangle_count"],"native_parts":len(observed["parts"]),"native_faces":sum(len(p["faces"]) for p in observed["parts"]),"stage_count":len(request(client,base,uri+"/stages")["stages"]),"qa_step_pass":True,"qa_stl_pass":True,"semantic_mapping_pass":job["qa"]["qa-step"]["semantic_mapping_pass"],"part_errors":[{k:p[k] for k in ("part_id","relative_volume_error","centroid_error_m","implicit_residual_max_m","reverse_max_m","topology_pass","semantic_mapping_pass")} for p in job["qa"]["qa-step"]["parts"]],"named_selections":len(context["named_selections"]),"interfaces":len(context["interfaces"]),"material_regions":len(contract["handoff"]["material_regions"]),"reviewer_distinct":review["record"]["reviewer_user_id"]!=review["record"]["build_creator_user_id"],"review_source_declares_synthetic":"Synthetic" in review["record"]["command"]["qualification_source"],"study_current":setup["upstream_current"],"study_execution_status":contract["execution_status"],"study_mesh_status":contract["mesh_status"],"solver_supported":False,"physical_validation":"NOT_PERFORMED","baseline_unchanged":True,"model_head_version":4,"section":section["section"],"downloads":proofs}
    if args.label=="after-restart":
        before=json.loads((directory/"ui-proof-before-restart.json").read_bytes());assert before["downloads"]==proofs and before["source_commit_id"]==result["source_commit_id"]
        result["identical_retained_originals_after_restart"]=True
    (directory/("ui-proof-"+args.label+".json")).write_text(json.dumps(result,indent=2)+"\n")
    print(args.label+":",result["native_parts"],"actual native bodies;",result["native_triangles"],"triangles;",len(proofs),"browser downloads byte-identical; study is setup only.")


if __name__=="__main__": main()
