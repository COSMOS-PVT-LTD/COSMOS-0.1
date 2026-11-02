"""Compare actual GUI downloads with retained authority, never live owner data."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.cycle_assessment import evaluate, methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal
from systems.projects.cycle_assessment import ManagedCycleAssessment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "record", "inputs", "csv", "plot", "plot_csv", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    # The qualified chart exporter admits up to16MiB, including the first-row
    # exact canonical source. Do not truncate it to Python csv's128KiB default.
    csv.field_size_limit(16 * 1024 * 1024)
    for name in ("record", "inputs", "csv", "plot", "plot_csv"):
        assert getattr(args, name).stat().st_size <= 16 * 1024 * 1024
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06_3_4-qa."):
        raise SystemExit("Only task-owned synthetic QA roots are allowed.")
    with sqlite3.connect(
        "file:" + str(root / "auth/users.sqlite") + "?mode=ro", uri=True
    ) as connection:
        row = connection.execute(
            "SELECT user_id,role,active FROM users WHERE login_id='r06-cycle-qa'"
        ).fetchone()
    actor = Principal(row[0], row[1], bool(row[2]))
    repo = SQLiteProjectRepository(root / "engineering_state/v1")
    raw = args.record.read_bytes()
    record = json.loads(raw)
    with args.csv.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    project, commit = rows[0]["project_id"], rows[0]["commit_id"]
    saved = repo.resolve_snapshot(actor, project, commit)
    assert saved.payload == raw and saved.head.content_hash == sha256(raw).hexdigest()
    inputs = repo.resolve_snapshot(actor, project, record["capture_commit_id"])
    assert inputs.payload == args.inputs.read_bytes()
    baseline = repo.resolve_snapshot(actor, project, record["baseline_commit_id"])
    assert baseline.payload.decode() == record["baseline_canonical_json"]
    assert (
        repo.get_snapshot(
            actor, project, domain=baseline.domain, object_id=baseline.object_id
        ).payload
        == baseline.payload
    )
    residuals = record["evaluation"]["result"]["outputs"]["residuals"]
    assert len(rows) == len(residuals)
    for row, original in zip(rows, residuals, strict=True):
        assert row["name"] == original["name"] and row["unit"] == original["unit"]
        assert (
            float(row["value"]) == original["value"]
            and float(row["tolerance"]) == original["tolerance"]
        )
        assert (
            row["content_sha256"] == saved.head.content_hash
            and row["commit_id"] == commit
        )
    plot = json.loads(args.plot.read_bytes())
    assert plot["source"]["source_canonical_json"].encode() == raw
    assert plot["source"]["commit_id"] == commit
    assert plot["source"]["content_sha256"] == saved.head.content_hash
    assert len(plot["rows"]) == len(residuals)
    for row, original in zip(plot["rows"], residuals, strict=True):
        assert (
            row["raw_value"] == original["value"]
            and row["raw_unit"] == original["unit"]
        )
        assert row["normalized"] == original["value"] / original["tolerance"]
    with args.plot_csv.open(newline="") as stream:
        plotted = list(csv.DictReader(stream))
    assert len(plotted) == len(residuals) * 3
    assert all(row["commit_id"] == commit for row in plotted)
    envelope = ManagedCycleAssessment(repo, evaluate, methods).read(actor, saved)
    assert envelope["usable_current_balanced_assessment"]
    result = {
        "scope": "Actual GUI-produced synthetic software assessment, not hardware evidence",
        "project_id": project,
        "object_id": saved.object_id,
        "commit_id": commit,
        "capture_commit_id": inputs.commit_id,
        "baseline_commit_id": baseline.commit_id,
        "content_sha256": saved.head.content_hash,
        "exact_record_input_bytes": True,
        "all_raw_and_normalized_residual_values": True,
        "baseline_unchanged": True,
        "current_balanced_assessment": True,
        "physical_validation": "NOT_PERFORMED",
        "files": {
            name: {
                "path": str(getattr(args, name)),
                "sha256": sha256(getattr(args, name).read_bytes()).hexdigest(),
            }
            for name in ("record", "inputs", "csv", "plot", "plot_csv")
        },
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        f"GUI export proof PASS: {len(residuals)} raw residuals, {len(plotted)} plot points; commit {commit}"
    )


if __name__ == "__main__":
    main()
