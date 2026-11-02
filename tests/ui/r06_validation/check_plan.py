"""Verify actual GUI plan/template downloads in an isolated synthetic QA root."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sqlite3
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.propulsion_validation import methods
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal
from systems.projects.propulsion_validation import (
    ASSESSMENT,
    DATA,
    PLAN,
    PropulsionValidation,
)
from validation import propulsion as vv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "record", "restart_record", "csv", "metadata", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06_3_4-qa.validation."):
        raise SystemExit("Only the task-owned synthetic validation QA root is allowed.")
    with sqlite3.connect(
        "file:" + str(root / "auth/users.sqlite") + "?mode=ro", uri=True
    ) as connection:
        user = connection.execute(
            "SELECT user_id,role,active FROM users WHERE login_id='r06-cycle-qa'"
        ).fetchone()
    assert user is not None
    actor = Principal(user[0], user[1], bool(user[2]))
    repo = SQLiteProjectRepository(root / "engineering_state/v1")
    saved = repo.resolve_snapshot(actor, args.project, args.commit)
    assert saved.domain == PLAN
    raw = args.record.read_bytes()
    assert raw == saved.payload == args.restart_record.read_bytes()
    assert sha256(raw).hexdigest() == saved.head.content_hash
    value = PropulsionValidation(repo, methods).read(actor, saved)
    record = value["record"]
    assert value["upstream_current"]
    assert record["readiness"] == "AWAITING_MEASUREMENTS"
    assert value["physical_validation"] == "NOT_PERFORMED"
    assert value["independent_acceptance"] is False
    candidate = record["candidate"]
    baseline = repo.resolve_snapshot(
        actor, args.project, candidate["baseline_commit_id"]
    )
    assert baseline.payload.decode() == candidate["baseline_canonical_json"]
    assert baseline.head.content_hash == candidate["baseline_sha256"]
    assert repo.get_snapshot(
        actor, args.project, domain=baseline.domain, object_id=baseline.object_id
    ).payload == baseline.payload
    assert args.csv.read_bytes() == vv.template(record)
    rows = list(csv.DictReader(io.StringIO(args.csv.read_text())))
    assert rows and all(row["value"] == row["standard_uncertainty"] == "" for row in rows)
    metadata = json.loads(args.metadata.read_bytes())
    assert set(metadata) == vv.PROVENANCE and all(value == "" for value in metadata.values())
    assert all(
        target["prediction_standard_uncertainty"] is None
        for target in record["specification"]["targets"].values()
    )
    assert not repo.list_objects(actor, args.project, domain=DATA)
    assert not repo.list_objects(actor, args.project, domain=ASSESSMENT)
    result = {
        "scope": "Actual GUI synthetic plan-preparation test, not hardware criteria or evidence",
        "qa_root": str(root),
        "project_id": args.project,
        "commit_id": saved.commit_id,
        "content_sha256": saved.head.content_hash,
        "current_source_methods": True,
        "original_and_restart_download_bytes_exact": True,
        "baseline_unchanged": True,
        "blank_template_rows": len(rows),
        "all_measured_values_and_uncertainties_empty": True,
        "metadata_all_empty": True,
        "prediction_uncertainty": "UNKNOWN",
        "measurement_records": 0,
        "assessment_records": 0,
        "readiness": record["readiness"],
        "physical_validation": "NOT_PERFORMED",
        "independent_acceptance": False,
        "files": {
            name: {
                "path": str(getattr(args, name)),
                "sha256": sha256(getattr(args, name).read_bytes()).hexdigest(),
            }
            for name in ("record", "restart_record", "csv", "metadata")
        },
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"GUI plan/template/restart proof PASS: {len(rows)} blank rows; no measurements or acceptance")


if __name__ == "__main__":
    main()
