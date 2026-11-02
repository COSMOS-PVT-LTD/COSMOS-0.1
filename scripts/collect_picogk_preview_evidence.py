"""Hash-checked read-only inspection of a task copy; no application lease/write."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("root","output"):p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--job",required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[1];root=a.root.resolve();out=a.output.resolve()
    if repo/"output" not in root.parents or repo/"output" not in out.parents or out.exists():raise ValueError("Existing isolated task root and NEW output required")
    store=root/"engineering_state/v1"
    with sqlite3.connect((store/"metadata.sqlite3").as_uri()+"?mode=ro",uri=True) as db:
        db.row_factory=sqlite3.Row
        job=dict(db.execute("SELECT * FROM durable_jobs WHERE job_id=?",(a.job,)).fetchone())
        event=dict(db.execute("SELECT * FROM durable_job_events WHERE job_id=? ORDER BY sequence DESC LIMIT 1",(a.job,)).fetchone())
        source=dict(db.execute("SELECT * FROM commits WHERE commit_id=?",(job["source_commit_id"],)).fetchone())
        blobs=[dict(r) for r in db.execute("SELECT * FROM durable_job_blobs WHERE job_id=? ORDER BY name",(a.job,))]
    def read(row):
        path=store/"blobs"/row["content_hash"];raw=path.read_bytes()
        if path.is_symlink() or len(raw)!=row["byte_length"] or sha256(raw).hexdigest()!=row["content_hash"]:raise ValueError("Stored bytes/hash mismatch")
        return raw
    record=read(event);inputs=read(source);value=json.loads(record);proof=json.loads(value["evidence_json"])
    for b in blobs:read(b)
    parts=proof.get("qa-stl",{}).get("parts",[])
    summary={"job":job,"state":event["state"],"source_root":str(root),"event_sha256":event["content_hash"],"inputs_sha256":source["content_hash"],"attachments":blobs,
        "part_count":len(parts),"software_qa_pass":proof.get("qa-stl",{}).get("pass"),"process":proof.get("process"),"worker_observations":proof.get("worker_observations"),
        "max_relative_volume_error":max((p["relative_volume_error"] for p in parts),default=None),"max_forward_residual_m":max((p["forward_max_m"] for p in parts),default=None),"max_reverse_distance_m":max((p["reverse_max_m"] or 0 for p in parts),default=None),
        "physical_validation":"NOT_PERFORMED","owner_root_modified":False,"scope":"Read-only retained evidence from an explicitly isolated task copy, not a complete/hardware-ready engine"}
    out.mkdir(parents=True)
    for name,raw in (("durable-record.json",record),("captured-inputs.json",inputs),("summary.json",json.dumps(summary,indent=2,allow_nan=False).encode())):
        with (out/name).open("xb") as f:f.write(raw)
    print({"state":summary["state"],"parts":len(parts),"software_qa_pass":summary["software_qa_pass"],"output":str(out)})


if __name__=="__main__":main()
