"""Verify actual browser downloads against a retained task-only source."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import Principal
from systems.projects.sensitivity import DOMAIN


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--prefix", default="sensitivity-actual")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if (
        not str(root).startswith("/private/tmp/cosmos-r06-qa.")
        or not (root / "engineering_state/v1/metadata.sqlite3").is_file()
    ):
        raise SystemExit(
            "Only an existing explicit R06 task-owned QA store is permitted."
        )
    connection = sqlite3.connect(
        "file:" + str(root / "auth/users.sqlite") + "?mode=ro", uri=True
    )
    try:
        account = connection.execute(
            "SELECT user_id,role,active FROM users WHERE login_id='r06-qa'"
        ).fetchone()
    finally:
        connection.close()
    actor = Principal(account[0], account[1], bool(account[2]))
    actor.require()
    files = {
        suffix: args.evidence / (args.prefix + suffix)
        for suffix in (".csv", ".svg", ".source.json", ".provenance.json")
    }
    plot = json.loads(files[".source.json"].read_text())
    source = plot["source"]
    repo = SQLiteProjectRepository(root / "engineering_state/v1")
    saved = repo.resolve_snapshot(actor, source["project_id"], source["commit_id"])
    assert (
        saved.domain == DOMAIN
        and sha256(saved.payload).hexdigest() == source["content_sha256"]
    )
    assert source["source_canonical_json"].encode() == saved.payload
    value = json.loads(saved.payload)
    expected = [
        [row["value"], row["output"]]
        for row in value["samples"]
        if row["status"] == "EVALUATED"
    ]
    assert plot["series"][0]["points"] == expected
    csv.field_size_limit(16 * 1024**2)
    with files[".csv"].open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(expected)
    assert all(
        row["project_id"] == source["project_id"]
        and row["baseline_commit_id"] == value["baseline_commit_id"]
        and row["commit_id"] == saved.commit_id
        for row in rows
    )
    assert (
        json.loads(rows[0]["source_json_first_row"])["source_canonical_json"].encode()
        == saved.payload
    )
    x = plot["x"]["label"] + " [" + plot["x"]["unit"] + "]"
    y = plot["y"]["label"] + " [" + plot["y"]["unit"] + "]"
    assert [[float(row[x]), float(row[y])] for row in rows] == expected
    svg = ET.fromstring(files[".svg"].read_bytes())
    assert svg.tag.endswith("svg") and list(svg.iter())
    metadata = json.loads(files[".provenance.json"].read_text())
    assert metadata["source"]["source_canonical_json"].encode() == saved.payload
    assert metadata["source"]["validation"] == "NOT_PERFORMED"
    result = {
        "scope": "Actual UI-generated software QA sensitivity exports, not hardware evidence",
        "project_id": source["project_id"],
        "commit_id": saved.commit_id,
        "baseline_commit_id": value["baseline_commit_id"],
        "retained_canonical_sha256": saved.head.content_hash,
        "requested_points": len(expected),
        "csv_exact_points_and_original_canonical_bytes": True,
        "svg_xml_and_provenance_original_bytes": True,
        "files": {
            key: {
                "bytes": path.stat().st_size,
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
            for key, path in files.items()
        },
    }
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(
        "PASS: actual CSV/SVG/source/provenance downloads match retained source and all requested points."
    )


if __name__ == "__main__":
    main()
