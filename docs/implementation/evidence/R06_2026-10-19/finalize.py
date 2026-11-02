"""Retain current R06.1a source/tests evidence; not a release or physical seal."""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EDITS = {
    "api/context_projects.py",
    "api/project_authority.py",
    "gui/server.py",
    "gui/static/projects.js",
    "gui/static/rocket-workbench/view.js",
    "gui/static/visualization/chart.js",
    "gui/static/visualization/exports.js",
    "gui/static/visualization/view.js",
    "tests/js/scientific_chart.test.cjs",
}


def main():
    entry = json.loads((HERE / "entry.json").read_text())
    changed = {
        name
        for name, digest in entry["sha256"].items()
        if sha256((ROOT / name).read_bytes()).hexdigest() != digest
    }
    assert changed == EDITS, changed ^ EDITS
    assert not any(
        name.startswith(("physics/", "core/", "numerics/", "systems/"))
        for name in changed
    )
    preservation = json.loads((HERE / "preservation-final.json").read_text())
    assert preservation["pass"]
    suites = ET.parse(HERE / "full-qualified-python.xml").getroot()
    assert not list(suites.iter("failure")) and not list(suites.iter("error"))
    cases = list(suites.iter("testcase"))
    assert "fail 0" in (HERE / "js-final.log").read_text()
    assert "All checks passed!" in (HERE / "ruff-final.log").read_text()
    assert "Success:" in (HERE / "mypy-final.log").read_text()
    assert not (HERE / "typescript-final.log").read_bytes()
    assert not (HERE / "whitespace-final.log").read_bytes()
    proof = json.loads((HERE / "final-export-proof.json").read_text())
    console = json.loads((HERE / "browser-console.json").read_text())
    assert not any(row["level"] == "error" for row in console)
    restart = (HERE / "ui-after-restart.txt").read_text()
    assert (
        proof["commit_id"] in restart
        and proof["retained_canonical_sha256"] in restart
        and "3/3 displayed source points" in restart
    )
    sources = {}
    for directory in (
        "core",
        "physics",
        "numerics",
        "systems",
        "simulation",
        "validation",
        "api",
        "gui",
        "infrastructure",
        "plugins",
        "tests",
        "scripts",
    ):
        for path in sorted((ROOT / directory).rglob("*")):
            if (
                path.is_file()
                and not path.is_symlink()
                and path.suffix in {".py", ".js", ".cjs", ".ts", ".css", ".html"}
            ):
                sources[str(path.relative_to(ROOT))] = sha256(
                    path.read_bytes()
                ).hexdigest()
    result = {
        "phase": "R06",
        "status": "PARTIAL",
        "slice": "R06.1a_assumed_state_sensitivity",
        "slice_status": "PASS_LOCAL_DECLARED_SCOPE",
        "approved_cycle_scope": [
            "steady single-phase pressure-fed first",
            "gas-generator next",
        ],
        "cycle_models_implemented": False,
        "requirements": {
            "RKT-01": "PARTIAL_FIRST_ASSUMED_STATE_SLICE",
            "RKT-02": "PLANNED",
            "RKT-03": "APPROVED_PLANNED",
            "RKT-04": "APPROVED_PLANNED",
            "RKT-05": "OUTSIDE_SELECTED_SCOPE_UNSUPPORTED",
            "RKT-06": "OUTSIDE_SELECTED_SCOPE_UNSUPPORTED",
            "RKT-07": "OUTSIDE_SELECTED_SCOPE_UNSUPPORTED",
            "RKT-08": "PLANNED",
        },
        "baseline_passed": 38,
        "focused_natural_order_passed": 47,
        "python": {
            "passed": sum(t.find("skipped") is None for t in cases),
            "skipped": len(list(suites.iter("skipped"))),
            "skip_reasons": dict(
                Counter(t.attrib.get("message", "") for t in suites.iter("skipped"))
            ),
        },
        "javascript_passed": 402,
        "mypy_source_files": 383,
        "ruff": "PASS",
        "strict_typescript_consumers": 7,
        "entry_sources": len(entry["sha256"]),
        "entry_unchanged": len(entry["sha256"]) - len(changed),
        "declared_edits": sorted(changed),
        "existing_scientific_sources_unchanged": True,
        "original_audit_preservation": {
            "unchanged": preservation["unchanged"],
            "declared_changes": len(preservation["declared_phase_changes"]),
            "unexpected": len(preservation["unexpected_changes"]),
            "missing": len(preservation["missing"]),
        },
        "actual_browser_export_restart": "PASS",
        "native_window_qualification": "NOT_RUN",
        "live_owner_data_changed": False,
        "commit_push_release": False,
        "physical_validation": "NOT_PERFORMED",
        "next": "R06.2 pressure-fed model/reference contracts; remaining sensitivity scope tracked separately",
    }
    (HERE / "STATUS.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "source-final.json").write_text(
        json.dumps(
            {
                "scope": "R06.1a software source identities only; no release/physical seal",
                "head": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "sha256": sources,
                "entry_scientific_parity": True,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "phase": result["status"],
                "slice": result["slice_status"],
                "python": result["python"]["passed"],
                "skipped": result["python"]["skipped"],
                "source_files": len(sources),
            }
        )
    )


if __name__ == "__main__":
    main()
