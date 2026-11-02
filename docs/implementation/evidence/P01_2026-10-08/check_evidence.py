"""P01 source-preservation and artifact checks; writes only P01 evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PREFIX = str(OUT.relative_to(ROOT)) + "/"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    baseline_path = OUT / "source_before.json"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    p00 = json.loads((OUT.parent / "P00_2026-10-08/source_hashes.json").read_text())
    p00_changed = [p for p, sha in p00.items() if not (ROOT / p).is_file() or digest(ROOT / p) != sha]
    assert not p00_changed, f"P00 source drift requires reassessment: {p00_changed}"
    if "--capture" in sys.argv:
        assert not baseline_path.exists(), "Do not replace the original P01 source checkpoint"
        paths = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
        hashes = {p: digest(ROOT / p) for p in sorted(set(paths))
                  if not p.startswith(PREFIX) and (ROOT / p).is_file()}
        baseline = {"commit_sha": head, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                    "hashes": hashes, "p00_source_drift": p00_changed}
        baseline_path.write_text(json.dumps(baseline, indent=2) + "\n")
        print(json.dumps({"source_files": len(hashes), "p00_source_drift": p00_changed, "sha": head}))
        return
    baseline = json.loads(baseline_path.read_text())
    changed = [p for p, sha in baseline["hashes"].items()
               if not (ROOT / p).is_file() or digest(ROOT / p) != sha]
    assert head == baseline["commit_sha"] and not changed, f"Out-of-scope changes: {changed}"
    current = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    unexpected = [p for p in set(current) if not p.startswith(PREFIX)
                  and p not in baseline["hashes"] and (ROOT / p).is_file()]
    assert not unexpected, f"New files outside P01: {unexpected}"
    navigation = json.loads((OUT / "navigation.json").read_text())
    registered = json.loads((OUT.parent / "P00_2026-10-08/workbench_inventory.json").read_text())
    assert {x["workbench_id"] for x in registered} == {x["id"] for x in navigation["compatibility_catalog"]}
    assert len(navigation["primary"]) == 7
    assert len({x["id"] for x in navigation["primary"]}) == 7
    workflow = json.loads((OUT.parent / "P00_2026-10-08/workflow_inventory.json").read_text())
    stage_ids = [stage for group in navigation["rocket_groups"] for stage in group["stage_ids"]]
    assert len(stage_ids) == 17 and len(set(stage_ids)) == 17
    assert set(stage_ids) == {item["stage_id"] for item in workflow["nodes"]}
    for p in ("P01_NAVIGATION_SPEC.md", "P01_TASK_FLOWS.md", "P01_WIREFRAMES.md",
              "P01_ACCESSIBILITY_PLAN.md", "P01_MIGRATION_SEAMS.md", "P01_REVIEW_RECORD.md",
              "prototype/index.html", "prototype/prototype.css", "prototype/prototype.js",
              "prototype/model.js", "prototype/model.test.cjs"):
        assert (OUT / p).is_file(), p
    # Check repository-relative Markdown links without mistaking Mermaid/inline code for links.
    import re
    broken = []
    for document in OUT.glob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if not target.startswith(("http", "#")) and not (document.parent / target.split("#")[0]).exists():
                broken.append({"document": document.name, "target": target})
    assert not broken, broken
    observations = json.loads((OUT / "browser-observations.json").read_text())
    observed = {entry["scenario"]: entry for entry in observations}
    def probe(name: str):
        return observed[name]["observed"]
    checks = [
        probe("preflight recovery focus")["focus"] == "ambientPa",
        observed["density mode invariants"]["unchanged"],
        probe("new revision and upstream old input inspection")["context"] == "Active demo-r2 · inspect demo-r1",
        probe("immediate draft invalidation")["result"] == "STALE · demo-r1",
        probe("QA rejection")["exportDisabled"],
        "CancelRequested" in probe("cancellation requested before acknowledgement"),
        "INSUFFICIENT_EVIDENCE" in probe("missing source"),
        probe("command escape restoration")["focus"] == "command-open",
        probe("reset default focus") == "reset-cancel",
        "demo-r2" in probe("reset cancelled preserves revision")["revision"],
        probe("collapsed panel layout")["inspectorHidden"] and probe("collapsed panel layout")["activityHidden"],
        probe("layout preferences survive reload")["inspectorHidden"] and probe("layout preferences survive reload")["activityHidden"],
        probe("hotkey command open")["open"] and probe("hotkey command open")["focus"] == "command-search",
        probe("minimum desktop context and overflow")["scrollWidth"] == probe("minimum desktop context and overflow")["clientWidth"],
        probe("command reverse-tab after explicit wrap fix")["inDialog"] and probe("command reverse-tab after explicit wrap fix")["focus"] == "command-close",
        probe("command forward-tab wrap after fix")["inDialog"] and probe("command forward-tab wrap after fix")["focus"] == "command-search",
        probe("rerendered action focus retained after fix") == "fixture-current",
    ]
    assert all(checks), f"Browser invariant failures: {[i + 1 for i, ok in enumerate(checks) if not ok]}"
    result = {"commit_sha": head, "p00_source_drift": p00_changed, "original_files_changed": changed,
              "primary_destinations": 7, "legacy_routes_preserved_in_spec": len(registered),
              "rocket_stages_preserved_in_spec": len(stage_ids), "unexpected_out_of_scope_files": unexpected,
              "browser_invariants_passed": len(checks), "browser_observation_records": len(observations),
              "broken_markdown_links": broken, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "P01 prototype/documents only; no production shell/data migration test claimed"}
    (OUT / "source_integrity.json").write_text(json.dumps(result, indent=2) + "\n")
    gate = {"gate_id": "G1", "phase": "P01_EXPERIENCE_ARCHITECTURE", "date": "2026-10-08",
            "commit_sha": head, "decision": "PENDING_OWNER_REVIEW", "phase_status": "PARTIAL",
            "requirements_addressed": ["P01 navigation, persona tasks, journeys, wireframes, accessibility plan, migration seams, approval record"],
            "prototype_model_tests_passed": 17, "browser_invariants_passed": len(checks),
            "production_files_changed": [], "human_acceptance": None,
            "approved_architecture_changes": [], "scientific_behavior_changes": [],
            "blockers": ["Owner review/acceptance of proposed experience architecture is outstanding"],
            "p03_production_ui_ready": False, "p02_independently_eligible_after_g0": True,
            "next_prompt": "P02_PICOGK_FEASIBILITY", "p02_started": False,
            "review_record": "P01_REVIEW_RECORD.md", "release_ready": False}
    (OUT / "G1_DECISION.json").write_text(json.dumps(gate, indent=2) + "\n")
    evidence_groups = [
        ("P01-E01", ["GOV-001", "GOV-006"], "Original source preserved; no approved architecture amendment inferred", ["source_integrity.json", "P01_SCOPE_AND_PLAN.md", "P01_MIGRATION_SEAMS.md"]),
        ("P01-E02", ["UX-001", "UX-005", "GOV-003"], "Persistent and distinct active/inspected context proposed; immutable example lineage is synthetic", ["P01_NAVIGATION_SPEC.md", "P01_TASK_FLOWS.md", "navigation.json", "browser-observations.json"]),
        ("P01-E03", ["UX-002", "UX-003", "GOV-004", "GOV-009"], "Unit-bearing inputs and independent status dimensions; unsupported real operations disabled", ["prototype/model.js", "prototype/prototype.js", "prototype-tests.log", "P01_WIREFRAMES.md"]),
        ("P01-E04", ["UX-004", "GOV-009"], "Source/assumption inspection and explicit missing-evidence recovery", ["P01_TASK_FLOWS.md", "browser-observations.json", "screenshots/08-knowledge-missing-evidence.jpg"]),
        ("P01-E05", ["UX-006", "UX-007", "UX-008"], "Prototype keyboard/layout/safe reset spot checks; real worker responsiveness and full accessibility remain future gates", ["P01_ACCESSIBILITY_PLAN.md", "browser-observations.json", "source_integrity.json"]),
        ("P01-E06", ["GOV-008", "GOV-010"], "Typed negative paths and additive migration/rollback plan; not production rollback qualification", ["P01_MIGRATION_SEAMS.md", "prototype/model.test.cjs", "prototype-tests.log"]),
        ("P01-E07", ["G1"], "Navigation and prototypes ready; owner acceptance not fabricated", ["P01_REVIEW_RECORD.md", "G1_DECISION.json", "P01_PHASE_REPORT.md"]),
    ]
    environment = {"python_executable": sys.executable, "python": sys.version.split()[0],
                   "source_scope": "HEAD plus original dirty working tree; P00 drift checked", "browser": "Codex in-app browser",
                   "viewport_checks": ["1280x720 requested", "1100x700 requested"]}
    commands = ["node --test docs/implementation/evidence/P01_2026-10-08/prototype/model.test.cjs",
                "node --check <prototype/model.js and prototype/prototype.js>",
                "python <P01>/check_evidence.py", "ruff check <P01>/check_evidence.py", "git diff --check",
                "CUA real-browser synthetic task walkthrough; not production E2E"]
    register = {"gate_id": "G1", "requirement_ids": sorted({r for _, reqs, _, _ in evidence_groups for r in reqs}),
                "commit_sha": head, "environment": environment, "commands": commands,
                "test_artifacts": ["prototype-tests.log", "browser-observations.json", "source_integrity.json"],
                "reviewer": "Codex automated checks; human review pending", "decision": "PARTIAL / PENDING_OWNER_REVIEW",
                "date": "2026-10-08", "blockers": gate["blockers"],
                "claims": [{"claim_id": cid, "requirement_ids": reqs, "claim": claim,
                            "artifacts": [{"path": p, "sha256": digest(OUT / p)} for p in paths],
                            "status": "PROTOTYPE_OR_PLAN_ONLY", "confidence": "HIGH for stated limited scope"}
                           for cid, reqs, claim, paths in evidence_groups]}
    (OUT / "EVIDENCE_REGISTER.json").write_text(json.dumps(register, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
