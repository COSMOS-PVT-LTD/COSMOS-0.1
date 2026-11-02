"""Bind selected-cycle local qualification to exact sources and preservation."""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/implementation/evidence/R06_3_4_2026-10-20"
DECLARED_EDITS = {
    "systems/projects/pressure_fed.py",
    "api/context_projects.py",
    "api/pressure_fed_projects.py",
    "api/project_authority.py",
    "gui/server.py",
    "gui/static/projects.js",
    "gui/static/visualization/chart.js",
    "gui/static/visualization/exports.js",
}


def main():
    previous_path = (
        ROOT / "docs/implementation/evidence/R06_2B_2026-10-20/source-final.json"
    )
    previous = json.loads(previous_path.read_bytes())["sha256"]
    changed, missing = [], []
    for name, digest in previous.items():
        path = ROOT / name
        if not path.is_file():
            missing.append(name)
        elif sha256(path.read_bytes()).hexdigest() != digest:
            changed.append(name)
    unexpected = sorted(set(changed) - DECLARED_EDITS)
    hashes = {
        str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
        for directory in (
            "core",
            "knowledge",
            "numerics",
            "physics",
            "systems",
            "api",
            "gui",
            "infrastructure",
            "simulation",
            "validation",
            "plugins",
            "tests",
        )
        for path in sorted((ROOT / directory).rglob("*"))
        if path.is_file()
        and path.suffix in {".py", ".js", ".cjs", ".ts", ".css", ".html"}
    }
    (EVIDENCE / "source-final.json").write_text(
        json.dumps(
            {
                "scope": "R06.3/4 local qualification; not release/physical acceptance",
                "head": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "sha256": hashes,
            },
            indent=2,
        )
        + "\n"
    )
    preservation = {
        "preceding_source_manifest_sha256": sha256(
            previous_path.read_bytes()
        ).hexdigest(),
        "preceding_sources": len(previous),
        "unchanged": len(previous) - len(changed) - len(missing),
        "declared_edits": sorted(changed),
        "missing": missing,
        "unexpected": unexpected,
        "old_scientific_core_physics_numerics_changed": [
            name
            for name in changed
            if name.startswith(("core/", "physics/", "numerics/"))
        ],
        "pass": not missing and not unexpected,
    }
    (EVIDENCE / "preservation.json").write_text(
        json.dumps(preservation, indent=2) + "\n"
    )
    suites = (
        ET.parse(EVIDENCE / "full-python-qualified.xml").getroot().findall("testsuite")
    )
    counts = {
        key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    counts["passed"] = (
        counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    )
    old_cases = {
        (item.attrib["classname"], item.attrib["name"])
        for item in ET.parse(
            ROOT / "docs/implementation/evidence/R06_2B_2026-10-20/full-python.xml"
        )
        .getroot()
        .iter("testcase")
    }
    new_cases = {
        (item.attrib["classname"], item.attrib["name"])
        for item in ET.parse(EVIDENCE / "full-python-qualified.xml")
        .getroot()
        .iter("testcase")
    }
    (EVIDENCE / "test-summary.json").write_text(
        json.dumps(
            {
                "python": counts,
                "preceding_cases_missing": sorted(old_cases - new_cases),
                "new_cases": len(new_cases - old_cases),
                "skips_are_not_passes": True,
                "skips": sorted(
                    {
                        item.attrib.get("message", "")
                        for item in ET.parse(EVIDENCE / "full-python-qualified.xml")
                        .getroot()
                        .iter("skipped")
                    }
                ),
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"Preservation: {preservation['unchanged']} unchanged, {len(changed)} declared edits, {len(unexpected)} unexpected, {len(missing)} missing. Python: {counts}"
    )
    if (
        not preservation["pass"]
        or counts["failures"]
        or counts["errors"]
        or old_cases - new_cases
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
