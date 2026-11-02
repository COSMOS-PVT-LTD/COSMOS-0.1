"""Match actual UI downloads to task-owned retained source bytes and rows."""

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

from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal
from systems.projects.pressure_fed import DOMAIN, INPUTS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--prefix", default="ui-download")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if (
        not str(root).startswith("/private/tmp/cosmos-r06_2b-qa.")
        or not (root / "QA_STATE.json").is_file()
    ):
        raise SystemExit("Only the explicit existing task-owned QA root is permitted.")
    connection = sqlite3.connect(
        "file:" + str(root / "auth/users.sqlite") + "?mode=ro", uri=True
    )
    try:
        row = connection.execute(
            "SELECT user_id,role,active FROM users WHERE login_id='r06-feed-qa'"
        ).fetchone()
    finally:
        connection.close()
    actor = Principal(row[0], row[1], bool(row[2]))
    files = {
        suffix: args.evidence / (args.prefix + suffix)
        for suffix in ("-record.json", "-inputs.json", "-residuals.csv")
    }
    raw = files["-record.json"].read_bytes()
    record = json.loads(raw)
    rows = list(csv.DictReader(files["-residuals.csv"].open(newline="")))
    assert len(rows) == 2
    project, commit = rows[0]["project_id"], rows[0]["commit_id"]
    repo = SQLiteProjectRepository(root / "engineering_state/v1")
    saved = repo.resolve_snapshot(actor, project, commit)
    assert saved.domain == DOMAIN and saved.payload == raw
    assert saved.head.content_hash == sha256(raw).hexdigest()
    captured = repo.resolve_snapshot(actor, project, record["capture_commit_id"])
    assert (
        captured.domain == INPUTS
        and captured.payload == files["-inputs.json"].read_bytes()
    )
    baseline = repo.resolve_snapshot(actor, project, record["baseline_commit_id"])
    assert baseline.payload.decode() == record["baseline_canonical_json"]
    assert (
        repo.get_snapshot(
            actor, project, domain=baseline.domain, object_id=baseline.object_id
        ).payload
        == baseline.payload
    )
    expected = record["evaluation"]["result"]["outputs"]
    for row in rows:
        assert row["project_id"] == project and row["commit_id"] == commit
        assert row["content_sha256"] == saved.head.content_hash
        assert row["baseline_commit_id"] == baseline.commit_id
        assert row["capture_commit_id"] == captured.commit_id
        stream = expected["streams"][row["stream"]]
        for key, value in stream.items():
            if key in row and type(value) in {int, float}:
                assert float(row[key]) == value, key
        assert row["pressure_state"] == stream["pressure_state"]
        assert row["physical_validation"] == "NOT_PERFORMED"
    assert record["status"] == "COMPLETED" and not expected["workflow_cycle_complete"]
    result = {
        "scope": "Actual UI-generated software QA downloads only; no physical evidence",
        "project_id": project,
        "object_id": saved.object_id,
        "commit_id": commit,
        "baseline_commit_id": baseline.commit_id,
        "canonical_sha256": saved.head.content_hash,
        "exact_retained_originals": True,
        "all_two_stream_csv_numeric_values": True,
        "source_design_unchanged": True,
        "files": {
            key: {
                "sha256": sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for key, path in files.items()
        },
    }
    with args.output.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(
        "PASS: original input/result bytes, all CSV stream values/identities and unchanged baseline."
    )


if __name__ == "__main__":
    main()
