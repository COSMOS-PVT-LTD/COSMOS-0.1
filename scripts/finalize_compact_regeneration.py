"""Record this research campaign's actual outcomes, including blocked physics."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path


def finalize(campaign, store, output):
    if (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
    ):
        raise ValueError("New absolute closeout receipt required")

    def load(name):
        return json.loads((campaign / name).read_bytes())

    preflight = load("preflight.json")
    inspection = load("independent-inspection-final.json")
    analysis = load("matched-analysis-final.json")
    native = load("native-display-final.json")
    comparison = load("optimized-managed-comparison-v2.json")
    if (
        inspection["software_checks_pass"] is not True
        or native["pass"] is not True
        or comparison["passed"] is not True
        or inspection["recipe_sha256"] != preflight["recipe_sha256"]
        or analysis["provenance"]["recipe_sha256"] != preflight["recipe_sha256"]
    ):
        raise ValueError("Required exact-candidate software evidence did not pass")
    if analysis["matched_thermal_feed_solved"] or any(
        v is not None for v in analysis["solution"].values()
    ):
        raise ValueError(
            "Readiness assessment must not be promoted to a thermal solution"
        )
    domains = {
        "engine-development-baseline": "selection_commit_id",
        "engine-redesign-candidate": "candidate_commit_id",
        "engine-component-model": "component_source_commit_id",
    }
    with sqlite3.connect(
        (store / "metadata.sqlite3").as_uri() + "?mode=ro", uri=True
    ) as connection:
        for domain, key in domains.items():
            count = connection.execute(
                "SELECT COUNT(*) FROM objects WHERE project_id=? AND domain=? AND head_commit_id=?",
                (preflight["project_id"], domain, preflight[key]),
            ).fetchone()[0]
            if count != 1:
                raise ValueError(
                    "Selected owner-project head changed during isolated generation"
                )
    tests = []
    for name in ("all-focused-final.xml", "native-feature-tests.xml"):
        document = ET.parse(campaign / name).getroot()
        suites = (
            [document] if document.tag == "testsuite" else document.findall("testsuite")
        )
        counts = {
            key: sum(int(s.attrib.get(key, "0")) for s in suites)
            for key in ("tests", "failures", "errors", "skipped")
        }
        if counts["tests"] <= 0 or any(
            counts[key] for key in ("failures", "errors", "skipped")
        ):
            raise ValueError(
                "Selected focused checks must have no failures/errors/skips"
            )
        tests.append({"file": name, **counts})
    artifact_names = (
        "preflight.json",
        "research-input.json",
        "matched-analysis-final.json",
        "independent-inspection-final.json",
        "native-display-final.json",
        "optimized-managed-comparison-v2.json",
        "occt/manifest.json",
        "occt/UNQUALIFIED-assembly.step",
        "picogk-optimized-0p6mm/manifest.json",
        "picogk-optimized-0p6mm/UNQUALIFIED-export.stl",
        "picogk-optimized-0p6mm/UNQUALIFIED-source.vdb",
        "display/manifest.json",
        "display/DISPLAY-ONLY-export.stl",
        "all-focused-final.xml",
        "native-feature-tests.xml",
        "javascript-tests.log",
    )
    artifacts = {
        name: {
            "bytes": (campaign / name).stat().st_size,
            "sha256": sha256((campaign / name).read_bytes()).hexdigest(),
        }
        for name in artifact_names
    }
    for directory, names in (
        ("occt", ("UNQUALIFIED-assembly.step",)),
        (
            "picogk-optimized-0p6mm",
            ("UNQUALIFIED-export.stl", "UNQUALIFIED-source.vdb"),
        ),
        ("display", ("DISPLAY-ONLY-export.stl",)),
    ):
        source_manifest = load(directory + "/manifest.json")
        for name in names:
            if (
                artifacts[directory + "/" + name]["sha256"]
                != source_manifest["artifacts"][name]
            ):
                raise ValueError(
                    "Generated artifact changed after its manifest was written"
                )
    javascript_log = (campaign / "javascript-tests.log").read_text()
    passed = re.search(r"(?m)^[#ℹ]\s*pass\s+(\d+)\s*$", javascript_log)
    failed = re.search(r"(?m)^[#ℹ]\s*fail\s+(\d+)\s*$", javascript_log)
    if not passed or not failed or int(passed[1]) <= 0 or int(failed[1]) != 0:
        raise ValueError("Selected JavaScript run lacks a passing completion summary")
    value = {
        "schema": "cosmos.compact-regeneration-closeout.v1",
        "date": "2026-10-30",
        "status": "FULL_SAVED_CAD_REGENERATED_MATCHED_PHYSICS_BLOCKED",
        "request_fully_completed": False,
        "campaign": str(campaign),
        "source": {
            key: preflight[key]
            for key in (
                "project_id",
                "selection_commit_id",
                "candidate_commit_id",
                "component_source_commit_id",
                "baseline_commit_id",
                "recipe_sha256",
            )
        },
        "saved_source_heads_unchanged": True,
        "old_records_deleted": False,
        "app_installed": False,
        "cad": {
            "metal_groups": inspection["occt"]["solid_count"],
            "step_reimport": "PASS_SOFTWARE_CHECKS",
            "picogk_voxel_m": load("picogk-optimized-0p6mm/manifest.json")["result"][
                "voxel_m"
            ],
            "native_triangles": inspection["picogk"]["triangle_count"],
            "native_topology": "PASS_BASIC_CLOSED_ORIENTED_MESH_CHECKS",
            "maximum_observed_relative_part_volume_error": max(
                p["relative_volume_error"] for p in inspection["picogk"]["parts"]
            ),
            "display_triangles": native["display_triangles"],
            "engineering_accuracy_accepted": False,
        },
        "matched_thermal_feed_solved": False,
        "physics_blockers": sorted({b["code"] for b in analysis["blockers"]}),
        "focused_python_tests": tests,
        "python_passed": sum(t["tests"] for t in tests),
        "javascript_passed": int(passed[1]),
        "native_display": "PASS",
        "old_0p5mm_attempt": "TIMED_OUT_600S_INCOMPLETE_RETAINED",
        "r08": "ON_HOLD",
        "runtime_admission": "NOT_PERFORMED_FOR_COMPACT_EXTENSION",
        "engineering_acceptance": "NOT_PERFORMED",
        "physical_validation": "NOT_PERFORMED",
        "free_bytes_after": shutil.disk_usage(campaign).free,
        "artifacts": artifacts,
    }
    with output.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
    print(
        json.dumps(
            {
                "status": value["status"],
                "python_passed": value["python_passed"],
                "receipt": str(output),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    finalize(args.campaign, args.store, args.output)


if __name__ == "__main__":
    main()
