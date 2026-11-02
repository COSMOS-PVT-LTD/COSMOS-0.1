"""Exact-source preservation and isolated synthetic browser/download proof."""

from __future__ import annotations

import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/implementation/evidence/R07_NATIVE_INTEGRATION_2026-10-20"
PREVIOUS = ROOT / "docs/implementation/evidence/R06_FINISH_R07_START_2026-10-20"
EDITS = {"systems/geometry/qa.py", "systems/geometry/service.py", "systems/geometry/authority.py",
         "infrastructure/persistence/durable_jobs.py", "api/project_authority.py", "api/context_projects.py",
         "gui/server.py", "gui/static/projects.js", "tests/unit_tests/infrastructure/test_geometry_stages.py"}


def collect_sources():
    previous_path = PREVIOUS / "source-final.json"
    previous = json.loads(previous_path.read_bytes())["sha256"]
    hashes = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
              for directory in ("core", "physics", "numerics", "knowledge", "systems", "api", "gui", "infrastructure", "simulation", "validation", "plugins", "tests")
              for p in sorted((ROOT / directory).rglob("*"))
              if p.is_file() and p.suffix in {".py", ".js", ".cjs", ".ts", ".css", ".html"}}
    changed = sorted(name for name in previous if name in hashes and previous[name] != hashes[name])
    unexpected, missing = sorted(set(changed) - EDITS), sorted(set(previous) - set(hashes))
    report = {"preceding_manifest_sha256": sha256(previous_path.read_bytes()).hexdigest(), "preceding_sources": len(previous),
              "unchanged": len(previous) - len(changed) - len(missing), "declared_edits": changed, "unexpected": unexpected, "missing": missing,
              "new_sources": sorted(set(hashes) - set(previous)), "old_core_physics_numerics_changed": [name for name in changed if name.startswith(("core/", "physics/", "numerics/"))], "pass": not unexpected and not missing}
    (EVIDENCE / "source-final.json").write_text(json.dumps({"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "scope": "Dirty local selected-nozzle software, not remote CI/release/physical acceptance", "sha256": hashes}, indent=2) + "\n")
    (EVIDENCE / "preservation.json").write_text(json.dumps(report, indent=2) + "\n")
    xml = ET.parse(EVIDENCE / "full-python-verified.xml").getroot()
    counts = {key: sum(int(s.attrib.get(key, 0)) for s in xml.iter("testsuite")) for key in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    cases = {(r.attrib["classname"], r.attrib["name"]) for r in xml.iter("testcase")}
    old = {(r.attrib["classname"], r.attrib["name"]) for r in ET.parse(PREVIOUS / "full-python-final.xml").getroot().iter("testcase")}
    (EVIDENCE / "test-summary.json").write_text(json.dumps({"python": counts, "new_cases": len(cases - old), "preceding_cases_missing": sorted(old - cases), "skip_reasons": sorted({s.attrib.get("message", "") for s in xml.iter("skipped")}), "skips_are_not_passes": True}, indent=2) + "\n")
    print("Preservation:", report["unchanged"], "unchanged,", len(changed), "declared edits,", len(unexpected), "unexpected.", counts)
    if not report["pass"] or old - cases or counts["failures"] or counts["errors"]:
        raise SystemExit(1)


def collect_ui(args):
    from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
    from tests.integration_tests.gui.test_project_authority_http import (
        client_for,
        request,
    )
    state = json.loads((args.root / "QA_STATE.json").read_bytes())
    client = client_for(args.base, "r07-nozzle-qa", "Synthetic-Nozzle-QA-Only!", "ENGINEER")
    prefix = "/api/projects/" + state["project_id"] + "/engine-geometry-builds/" + args.object_id
    path = prefix + "/jobs/" + args.job
    job = request(client, args.base, path)
    downloads = [("record.json", path + "/record.json", "nozzle-build-record.json"), ("inputs.json", prefix + "/inputs.json", "nozzle-build-inputs.json"), ("export.step", path + "/blobs/export.step", "export.step"), ("export.stl", path + "/blobs/export.stl", "export.stl")]
    proofs = []
    downloaded = json.loads(args.download_map.read_bytes()) if args.download_map else {}
    for name, url, download in downloads:
        raw = binary(client, args.base, url)
        file = Path(downloaded[name]) if name in downloaded else Path("/Users/vaibhavkumarn/Downloads") / ("COSMOS-unreviewed-engine-candidate-" + download)
        proof = {"name": name, "server_sha256": sha256(raw).hexdigest(), "browser_download_sha256": sha256(file.read_bytes()).hexdigest(), "byte_length": len(raw), "equal": file.read_bytes() == raw}
        if not proof["equal"]:
            raise ValueError("Browser download differs from retained original: " + name)
        proofs.append(proof)
    preview = binary(client, args.base, path + "/preview")
    result = {"project_id": state["project_id"], "object_id": args.object_id, "job_id": args.job, "source_commit_id": job["source_commit_id"], "state": job["state"], "current_generated_candidate": job["current_generated_candidate"], "engineering_acceptance": job["engineering_acceptance"], "physical_validation": job["physical_validation"], "qa": job["qa"], "downloads": proofs, "preview_vertices": len(preview) // 12, "preview_sha256": sha256(preview).hexdigest(), "stage_count": len(request(client, args.base, path + "/stages")["stages"])}
    (EVIDENCE / ("ui-export-proof-" + args.label + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    print("Actual browser downloads match retained originals;", result["preview_vertices"], "display vertices; state", job["state"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--object-id")
    parser.add_argument("--job")
    parser.add_argument("--label", default="final")
    parser.add_argument("--download-map", type=Path)
    args = parser.parse_args()
    if args.root:
        if not str(args.root.resolve()).startswith("/private/tmp/cosmos-r07-nozzle-qa.") or not args.label.isalnum():
            raise ValueError("Task-owned synthetic QA root and bounded label required")
        collect_ui(args)
    else:
        collect_sources()


if __name__ == "__main__":
    main()
