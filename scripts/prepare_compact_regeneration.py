"""Export the exact selected compact candidate for isolated research generation.

Reads an existing authority store through SQLite read-only mode. Never selects a
different head, edits app data, admits a runtime, or resumes engineering release.
Generated evidence uses exclusive creation in a NEW directory.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sqlite3
from hashlib import sha256
from pathlib import Path

from scripts.generate_engine_redesign import preflight, unique
from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.geometry.component_model import from_contracts
from systems.geometry.engine_redesign import compile_candidate


def read_json(path):
    raw = path.read_bytes()
    if len(raw) > 2_097_152:
        raise ValueError("Bounded source record required")
    return json.loads(raw, object_pairs_hook=unique), sha256(raw).hexdigest()


def retained(connection, store, authority, domain):
    row = connection.execute(
        "SELECT o.head_commit_id,o.version,o.content_hash,c.byte_length "
        "FROM objects o JOIN commits c ON c.commit_id=o.head_commit_id "
        "WHERE o.project_id=? AND o.domain=? AND o.object_id=?",
        (authority["project_id"], domain, authority["object_id"]),
    ).fetchone()
    head = authority["head"]
    if row is None or tuple(row[:3]) != (
        authority["commit_id"],
        head["version"],
        head["content_hash"],
    ):
        raise ValueError(
            "Selected source/head changed; explicit reconciliation required"
        )
    path = store / "blobs" / row[2]
    if path.is_symlink():
        raise ValueError("Retained source must not traverse an alias")
    raw = path.read_bytes()
    if len(raw) != row[3] or sha256(raw).hexdigest() != row[2]:
        raise ValueError("Retained source content hash/length mismatch")
    return json.loads(raw, object_pairs_hook=unique)


def prepare(receipt_path, store, output, voxel_m):
    if not math.isfinite(voxel_m) or not 0.000025 <= voxel_m <= 0.002:
        raise ValueError("Explicit bounded research voxel size required")
    if not store.is_absolute() or store != store.resolve():
        raise ValueError("Explicit real existing authority store required")
    database = store / "metadata.sqlite3"
    if not database.is_file():
        raise ValueError("Existing authority database required; no initialization")
    preflight(output)
    receipt, receipt_hash = read_json(receipt_path)
    if receipt.get("applied") is not True:
        raise ValueError("An applied development selection receipt is required")
    selection = receipt["baseline"]["authority"]
    source_ref = receipt["baseline"]["record"]["component_source"]
    source_ref = {**source_ref, "project_id": selection["project_id"]}
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        connection.execute("BEGIN")
        selected = retained(connection, store, selection, "engine-development-baseline")
        candidate_record = retained(
            connection, store, receipt["candidate"], "engine-redesign-candidate"
        )
        source = retained(connection, store, source_ref, "engine-component-model")
    if selected != receipt["baseline"]["record"]:
        raise ValueError("Selection receipt differs from retained authority")
    chosen = selected["selection"]
    expected_candidate = {
        "object_id": receipt["candidate"]["object_id"],
        "commit_id": receipt["candidate"]["commit_id"],
        "head": receipt["candidate"]["head"],
        "domain": "engine-redesign-candidate",
        "kind": "COMPACT_CANDIDATE",
    }
    if (
        chosen != expected_candidate
        or receipt["candidate"]["project_id"] != selection["project_id"]
        or candidate_record["source_object_id"] != source_ref["object_id"]
        or candidate_record["source_sha256"] != source_ref["head"]["content_hash"]
        or selected["propulsion_commit_id"] != source["baseline_commit_id"]
    ):
        raise ValueError(
            "Candidate authority does not match the selected development baseline"
        )
    research = receipt["research_input"]
    if (
        research["schema"] != "cosmos.compact-engine-input.v1"
        or research["source_commit_id"] != source_ref["commit_id"]
        or candidate_record["source_commit_id"] != source_ref["commit_id"]
        or research["specification"] != candidate_record["specification"]
        or research["source_model"]
        != {name: source[name] for name in ("snapshot_json", "graph_json")}
    ):
        raise ValueError(
            "Research input does not match the exact retained candidate/source"
        )
    model = research["source_model"]
    plan = from_contracts(
        DesignSnapshot.from_json(model["snapshot_json"]),
        GeometryFeatureGraph.from_json(model["graph_json"]),
    )
    candidate = compile_candidate(plan, research["specification"])
    wire = candidate.wire()
    if (
        not research["recipe_sha256"]
        == candidate_record["recipe_sha256"]
        == wire["recipe_sha256"]
    ):
        raise ValueError("Recipe changed; no silent recompilation of selected geometry")
    cells = sum(
        math.prod(
            (g["bounds_m"][i + 3] - g["bounds_m"][i]) / voxel_m + 5 for i in range(3)
        )
        for g in wire["groups"]
    )
    if cells > 120_000_000:
        raise ValueError("PicoGK field exceeds existing 120M-cell envelope")
    info = {
        "schema": "cosmos.compact-regeneration-preflight.v1",
        "selection_receipt_sha256": receipt_hash,
        "project_id": selection["project_id"],
        "selection_commit_id": selection["commit_id"],
        "candidate_commit_id": receipt["candidate"]["commit_id"],
        "component_source_commit_id": source_ref["commit_id"],
        "baseline_commit_id": source["baseline_commit_id"],
        "baseline_sha256": sha256(
            source["baseline_canonical_json"].encode()
        ).hexdigest(),
        "recipe_sha256": wire["recipe_sha256"],
        "voxel_m": voxel_m,
        "declared_cells": cells,
        "free_bytes_before": shutil.disk_usage(output.parent).free,
        "authority_heads_matched": True,
        "app_data_modified": False,
        "app_installed": False,
        "r08": "ON_HOLD",
        "engineering_acceptance": "NOT_PERFORMED",
        "physical_validation": "NOT_PERFORMED",
    }
    output.mkdir(mode=0o700)
    records = {
        "research-input.json": research,
        "preflight.json": info,
        "geometry-inspection.json": candidate.report(),
        "bound-propulsion-baseline.json": json.loads(source["baseline_canonical_json"]),
    }
    for name, record in records.items():
        with (output / name).open("x") as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-receipt", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voxel-m", type=float, required=True)
    args = parser.parse_args()
    info = prepare(args.selection_receipt, args.store, args.output, args.voxel_m)
    print(json.dumps({"ok": True, "output": str(args.output), **info}))


if __name__ == "__main__":
    main()
