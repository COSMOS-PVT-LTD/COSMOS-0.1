"""Preservation and test-identity receipt for selected engine operating closure."""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/"docs/implementation/evidence/R06_CLOSURE_2026-10-20"
PREVIOUS = ROOT/"docs/implementation/evidence/R06_VALIDATION_2026-10-20"
EDITS = {"api/project_authority.py","api/context_projects.py","gui/server.py","gui/static/projects.js","gui/static/managed-cycle.css","gui/static/visualization/chart.js","gui/static/visualization/exports.js"}


def main():
    previous_path = PREVIOUS/"source-final.json"
    previous = json.loads(previous_path.read_bytes())["sha256"]
    hashes = {
        str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest()
        for directory in ("core","physics","numerics","knowledge","systems","api","gui","infrastructure","simulation","validation","plugins","tests")
        for path in sorted((ROOT/directory).rglob("*"))
        if path.is_file() and path.suffix in {".py",".js",".cjs",".ts",".css",".html"}
    }
    missing = sorted(set(previous)-set(hashes))
    changed = sorted(name for name in previous if name in hashes and previous[name] != hashes[name])
    unexpected = sorted(set(changed)-EDITS)
    preservation = {"preceding_manifest_sha256":sha256(previous_path.read_bytes()).hexdigest(),"preceding_sources":len(previous),"unchanged":len(previous)-len(changed)-len(missing),"declared_edits":changed,"unexpected":unexpected,"missing":missing,"new_sources":sorted(set(hashes)-set(previous)),"old_physics_core_numerics_sources_changed":[name for name in changed if name.startswith(("physics/","core/","numerics/"))],"pass":not missing and not unexpected}
    head = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    (EVIDENCE/"source-final.json").write_text(json.dumps({"scope":"Local selected operating-model software qualification, not release/physical acceptance","head":head,"sha256":hashes},indent=2)+"\n")
    (EVIDENCE/"preservation.json").write_text(json.dumps(preservation,indent=2)+"\n")
    xml = ET.parse(EVIDENCE/"full-python-final.xml").getroot()
    counts = {key:sum(int(s.attrib.get(key,0)) for s in xml.findall("testsuite")) for key in ("tests","failures","errors","skipped")}
    counts["passed"] = counts["tests"]-counts["failures"]-counts["errors"]-counts["skipped"]
    cases = {(r.attrib["classname"],r.attrib["name"]) for r in xml.iter("testcase")}
    old_cases = {(r.attrib["classname"],r.attrib["name"]) for r in ET.parse(PREVIOUS/"full-python.xml").getroot().iter("testcase")}
    (EVIDENCE/"test-summary.json").write_text(json.dumps({"python":counts,"new_cases":len(cases-old_cases),"preceding_cases_missing":sorted(old_cases-cases),"skips_are_not_passes":True,"skip_reasons":sorted({s.attrib.get("message","") for s in xml.iter("skipped")}),"ci_workflow_sha256":sha256((ROOT/".github/workflows/ci.yml").read_bytes()).hexdigest()},indent=2)+"\n")
    print(f"Preservation: {preservation['unchanged']} unchanged, {len(changed)} declared edits, {len(missing)} missing, {len(unexpected)} unexpected. Python: {counts}")
    if not preservation["pass"] or old_cases-cases or counts["failures"] or counts["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
