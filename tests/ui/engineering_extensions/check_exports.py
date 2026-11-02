"""Compare actual UI downloads to isolated authority, including restart originals."""

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

from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.projects.authority import Principal
from validation import propulsion as vv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--blank-template", type=Path, required=True)
    args = parser.parse_args()
    root, downloads = args.root.resolve(), args.downloads.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06-operating-qa."):
        raise SystemExit("Only task-owned synthetic QA roots allowed.")
    csv.field_size_limit(16 * 1024 * 1024)
    with sqlite3.connect("file:" + str(root / "auth/users.sqlite") + "?mode=ro", uri=True) as conn:
        user = conn.execute("SELECT user_id,role,active FROM users WHERE login_id='r06-operating-qa'").fetchone()
    actor = Principal(user[0], user[1], bool(user[2]))
    repo = SQLiteProjectRepository(root / "engineering_state/v1")
    result = {"scope": "Actual browser/native/SQLite/download qualification over synthetic inputs only; no physical evidence", "qa_root": str(root), "physical_validation": "NOT_PERFORMED", "files": {}}

    def raw(name):
        path = downloads / name
        data = path.read_bytes()
        result["files"][name] = {"path": str(path), "sha256": sha256(data).hexdigest()}
        return data

    for kind, plot_name, prefix in (
        ("operating-sensitivity", "operating-sensitivity-0", "COSMOS-preliminary-model-operating-sensitivity"),
        ("engine-geometry-intent", "engine-nozzle-intent", "COSMOS-unbuilt-engine-intent-engine-geometry-intent"),
    ):
        plot = json.loads(raw(plot_name + ".source.json"))
        origin = plot["source"]
        saved = repo.resolve_snapshot(actor, origin["project_id"], origin["commit_id"])
        original = raw(prefix + "-record.json")
        # Both paths are real UI downloads, before and after server restart.
        assert original == saved.payload == raw(prefix + "-record (1).json")
        assert sha256(original).hexdigest() == origin["content_sha256"] == saved.head.content_hash
        assert origin["source_canonical_json"].encode() == original and origin["domain"] == kind
        assert json.loads(raw(plot_name + ".provenance.json"))["source"] == origin
        record = json.loads(original)
        captured = repo.resolve_snapshot(actor, saved.project_id, record["capture_commit_id"])
        assert captured.payload == raw(prefix + "-inputs.json")
        baseline = repo.resolve_snapshot(actor, saved.project_id, record["baseline_commit_id"])
        assert baseline.payload.decode() == record["baseline_canonical_json"]
        assert repo.get_snapshot(actor, saved.project_id, domain=baseline.domain, object_id=baseline.object_id).payload == baseline.payload
        assert repo.dependencies_current(actor, saved.project_id, saved.commit_id)
        out = record["evaluation"]["result"]["outputs"]
        assert not out["workflow_cycle_complete"] and out["physical_validation"] == "NOT_PERFORMED"
        if kind == "operating-sensitivity":
            assert out["study_status"] == "COMPLETED" and len(out["evaluations"]) == 5
            with (downloads / (prefix + "-residuals.csv")).open(newline="") as stream:
                cases = list(csv.DictReader(stream))
            raw(prefix + "-residuals.csv")
            for row, original_row in zip(cases, out["evaluations"], strict=True):
                assert float(row["value"]) == original_row["value"] and float(row["output"]) == original_row["output"]
                assert row["content_sha256"] == saved.head.content_hash and row["commit_id"] == saved.commit_id
            with (downloads / (plot_name + ".csv")).open(newline="") as stream:
                chart_rows = list(csv.DictReader(stream))
            raw(plot_name + ".csv")
            for row, original_row in zip(chart_rows, out["samples"], strict=True):
                assert float(row["fuel tank_pressure [Pa]"]) == original_row["value"]
                assert float(row["Core thrust [N]"]) == original_row["output"]
                assert row["commit_id"] == saved.commit_id
            assert plot["rows"] == [{"input": row["value"], "output": row["output"]} for row in out["samples"]]
            result[kind] = {"commit_id": saved.commit_id, "content_sha256": saved.head.content_hash, "cases": len(cases), "plot_samples": len(chart_rows), "derivatives": out["derivatives"], "refinement_difference_not_error_bound": out["step_refinement_absolute_difference"]}
        else:
            snapshot = DesignSnapshot.from_json(out["snapshot_json"])
            graph = GeometryFeatureGraph.from_json(out["graph_json"])
            graph.validate_snapshot(snapshot)
            assert snapshot.project_id.startswith("engine-design-") and snapshot.project_id != "p07-software-fixtures"
            assert graph.content_sha256 == out["graph_sha256"]
            assert plot["rows"] == out["profile"]
            assert not out["engineering_export_eligible"] and out["artifacts"] == [] and out["backend"] is None
            svg = raw(plot_name + ".svg").decode()
            dims = re.search(r'<svg\b[^>]*\bwidth="([0-9.]+)"[^>]*\bheight="([0-9.]+)"', svg)
            assert dims and float(dims[1]) > 0 and float(dims[2]) >= 300
            assert "UNBUILT engine geometry intent" in svg
            result[kind] = {"commit_id": saved.commit_id, "content_sha256": saved.head.content_hash, "snapshot_id": snapshot.snapshot_id, "profile_stations": len(out["profile"]), "feature_order": list(graph.topological_order()), "svg_dimensions": [float(dims[1]), float(dims[2])], "cad_built_or_accepted": False}
    plan_raw = raw(args.plan.name)
    plan = json.loads(plan_raw)
    plan_objects = repo.list_objects(actor, saved.project_id, domain="propulsion-validation-plan")
    assert len(plan_objects) == 1
    plan_source = repo.resolve_snapshot(actor, saved.project_id, plan_objects[0].commit_id)
    assert plan_source.payload == plan_raw
    assert plan["candidate"]["baseline_commit_id"] != record["baseline_commit_id"]  # operating record, not its old propulsion baseline
    assert plan["physical_validation"] == "NOT_PERFORMED" and plan["readiness"] == "AWAITING_MEASUREMENTS"
    with args.blank_template.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    raw(args.blank_template.name)
    assert len(rows) == len(vv.context_rows(plan["candidate"])) + len(plan["candidate"]["predictions"])
    assert rows and all(not row["value"] and not row["standard_uncertainty"] for row in rows)
    assert not repo.list_objects(actor, saved.project_id, domain="propulsion-measurement")
    assert not repo.list_objects(actor, saved.project_id, domain="propulsion-validation-assessment")
    result["validation_preparation"] = {"plan_commit_id": plan_source.commit_id, "blank_template_rows": len(rows), "measurements": 0, "assessments": 0, "blockers": plan["blockers"]}
    result["original_input_result_restart_and_export_bytes_exact"] = True
    result["baseline_unchanged"] = True
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("UI/export/restart proof PASS: five native sensitivity cases, engine-derived nozzle intent, empty solved-candidate evidence plan; no physical evidence.")


if __name__ == "__main__":
    main()
