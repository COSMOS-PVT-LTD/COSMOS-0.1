"""Check real GUI operating-model exports against isolated retained authority."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.engine_operating import evaluate, methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal
from systems.projects.engine_operating import ManagedEngineOperating


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "record", "restart_record", "inputs", "csv", "plot_csv", "plot_source", "plot_provenance", "svg", "output"):
        parser.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06-operating-qa."):
        raise SystemExit("Only task-owned synthetic operating QA roots allowed.")
    csv.field_size_limit(16*1024*1024)
    with sqlite3.connect("file:"+str(root/"auth/users.sqlite")+"?mode=ro",uri=True) as connection:
        user = connection.execute("SELECT user_id,role,active FROM users WHERE login_id='r06-operating-qa'").fetchone()
    actor = Principal(user[0],user[1],bool(user[2]))
    repo = SQLiteProjectRepository(root/"engineering_state/v1")
    plot = json.loads(args.plot_source.read_bytes())
    project,commit = plot["source"]["project_id"],plot["source"]["commit_id"]
    saved = repo.resolve_snapshot(actor,project,commit)
    raw = args.record.read_bytes()
    assert raw == saved.payload == args.restart_record.read_bytes()
    assert sha256(raw).hexdigest() == saved.head.content_hash
    value = ManagedEngineOperating(repo,evaluate,methods).read(actor,saved)
    assert value["usable_current_solved_candidate"]
    record = value["record"]
    inputs = repo.resolve_snapshot(actor,project,record["capture_commit_id"])
    assert inputs.payload == args.inputs.read_bytes()
    assert json.loads(inputs.payload)["command"]["specification"] == json.loads((root/"OPERATING_SPEC.json").read_bytes())
    baseline = repo.resolve_snapshot(actor,project,record["baseline_commit_id"])
    assert record["baseline_canonical_json"].encode() == baseline.payload
    assert repo.get_snapshot(actor,project,domain=baseline.domain,object_id=baseline.object_id).payload == baseline.payload
    output = record["evaluation"]["result"]["outputs"]
    assert output["numerical_convergence"] and output["conservation_checks"] == "PASS"
    assert output["physical_validation"] == "NOT_PERFORMED" and not output["workflow_cycle_complete"]
    with args.csv.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row,original in zip(rows,output["residuals"],strict=True):
        assert row["commit_id"] == commit and row["content_sha256"] == saved.head.content_hash
        assert float(row["value"]) == original["value"] and row["unit"] == original["unit"]
    assert plot["source"]["source_canonical_json"].encode() == raw
    assert plot["rows"] == output["solver"]["history"]
    provenance = json.loads(args.plot_provenance.read_bytes())
    assert provenance["source"] == plot["source"]
    with args.plot_csv.open(newline="") as stream:
        plot_rows = list(csv.DictReader(stream))
    assert len(plot_rows) == len(plot["rows"])
    for row,original in zip(plot_rows,plot["rows"],strict=True):
        assert row["commit_id"] == commit
        assert float(row["Accepted Newton iteration [1]"]) == original["iteration"]
        assert float(row["Operating-point normalized residual history [1]"]) == original["infinity_norm"]
    svg = args.svg.read_text()
    dimensions = re.search(r'<svg\b[^>]*\bwidth="([0-9.]+)"[^>]*\bheight="([0-9.]+)"',svg)
    assert dimensions and float(dimensions[1]) > 0 and float(dimensions[2]) >= 300
    assert "Operating-point normalized residual history" in svg
    # The established exporter binds SVG to the original via the separate
    # exact-source/provenance files, not invented inline SVG identity fields.
    result = {
        "scope":"Real GUI/native calculation over synthetic properties and boundaries; not hardware evidence",
        "qa_root":str(root),"project_id":project,"commit_id":commit,"content_sha256":saved.head.content_hash,
        "original_input_result_and_restart_bytes_exact":True,"baseline_unchanged":True,"all_residual_and_iteration_export_values_exact":True,
        "independent_residual_rows":len(rows),"nonlinear_history_samples":len(plot_rows),"thermal_history_samples":len(output["candidate"]["thermal_history"]),
        "current_solved_candidate":True,"physical_validation":"NOT_PERFORMED",
        "svg_nonzero_dimensions":[float(dimensions[1]),float(dimensions[2])],"svg_source_binding":"Paired complete provenance/source bundle; not standalone inline SHA metadata",
        "unknowns":output["candidate"]["unknowns"],"external_energy_ledger_w":output["candidate"]["external_energy_ledger_w"],
        "files":{name:{"path":str(getattr(args,name)),"sha256":sha256(getattr(args,name).read_bytes()).hexdigest()} for name in ("record","restart_record","inputs","csv","plot_csv","plot_source","plot_provenance","svg")},
    }
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(f"GUI/export/restart proof PASS: {len(rows)} independent residuals, {len(plot_rows)} nonlinear history samples; exact source {commit}")


if __name__ == "__main__":
    main()
