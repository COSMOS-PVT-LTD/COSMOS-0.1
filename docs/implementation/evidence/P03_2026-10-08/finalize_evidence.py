"""Build a hashed, scope-bound P03 evidence register; verify without claiming reruns."""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
P01 = HERE.parent / "P01_2026-10-08"
P02 = HERE.parent / "P02_2026-10-08"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def artifacts(paths):
    return [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in sorted(set(paths))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]


def check_results():
    report = json.loads((HERE / "browser-tests.json").read_text())
    assert report["stats"]["expected"] == 44
    assert report["stats"]["unexpected"] == report["stats"]["flaky"] == report["stats"]["skipped"] == 0
    for theme in ("dark", "high-contrast"):
        assert not json.loads((HERE / f"accessibility-{theme}.json").read_text())["violations"]
    suites = ET.parse(HERE / "logs/pytest.xml").getroot().findall("testsuite")
    totals = {key: sum(int(suite.get(key, "0")) for suite in suites) for key in ("tests", "failures", "errors", "skipped")}
    assert totals == {"tests": 2239, "failures": 0, "errors": 0, "skipped": 5}, totals
    assert "pass 57" in (HERE / "logs/js-tests-final.log").read_text()
    assert "fail 0" in (HERE / "logs/js-tests-final.log").read_text()
    assert "pass 34" in (HERE / "logs/design-system-unit-final.log").read_text()
    assert "All checks passed!" in (HERE / "logs/ruff-regression-final.log").read_text()
    assert "All checks passed!" in (HERE / "logs/ruff-phase-final.log").read_text()
    assert "no issues found in 318 source files" in (HERE / "logs/mypy.log").read_text()
    assert (HERE / "logs/typecheck-final.log").read_text() == ""
    assert json.loads((HERE / "source_integrity.json").read_text())["pass"]
    assert json.loads((P01 / "G1_DECISION.json").read_text())["decision"] == "ACCEPTED_BY_OWNER"
    assert json.loads((P02 / "P02_DECISION.json").read_text())["phasePassed"]
    return totals


def verify():
    check_results()
    for register in (HERE / "EVIDENCE_REGISTER.json", P02 / "completion/EVIDENCE_REGISTER.json"):
        data = json.loads(register.read_text())
        for artifact in data["artifacts"]:
            assert digest(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]
    assert json.loads((HERE / "G2_DECISION.json").read_text())["status"] == "PASS"
    print(json.dumps({"gate": "G2", "status": "PASS", "browserChecks": 44,
        "pythonPassed": 2234, "pythonSkipped": 5, "javascriptPassed": 57, "evidenceHashes": "PASS"}))


def build(tools):
    logs, tooling = HERE / "logs", HERE / "tooling"
    logs.mkdir(exist_ok=True)
    tooling.mkdir(exist_ok=True)
    for path in tools.glob("*.log"):
        shutil.copy2(path, logs / path.name)
    shutil.copy2(tools / "pytest.xml", logs / "pytest.xml")
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(tools / name, tooling / name)
    for name, relative in {"playwright": "@playwright/test/LICENSE", "axe-core": "axe-core/LICENSE",
        "typescript": "typescript/LICENSE.txt", "pngjs": "pngjs/LICENSE"}.items():
        shutil.copy2(tools / "node_modules" / relative, tooling / f"{name}-LICENSE.txt")
    integrity = subprocess.run([sys.executable, str(HERE / "check_scope.py")], cwd=ROOT, check=True,
        capture_output=True, text=True)
    (logs / "source-scope.log").write_text(integrity.stdout)
    totals = check_results()
    baseline = json.loads((HERE / "legacy-interaction-baseline.json").read_text())
    new = json.loads((HERE / "interaction-performance.json").read_text())
    assert new["unrelatedMutations"] == 0 and new["p95Ms"] <= baseline["maxMs"]
    write(HERE / "PERFORMANCE_BUDGET.json", {"scope": "Development-device synchronous input-handler fixture only",
        "samplesPerFixture": 50, "sourceBaseline": "legacy-interaction-baseline.json",
        "p95CeilingMs": baseline["maxMs"], "measuredP03P95Ms": new["p95Ms"], "withinMeasuredBudget": True,
        "unrelatedPlotTableMutationBudget": 0, "observedJsHeapBaselineBytes": new["jsHeapBytes"],
        "memoryPolicy": "Record this observed fixture heap baseline for future like-for-like comparison; not an RSS or full-app ceiling",
        "limitations": ["Synthetic synchronous dispatch; no paint/end-to-end SLA", "Timer quantization and browser GC",
            "10k in-memory arrays, bounded DOM only", "P04 must rebaseline real integrated state and viewport work"]})
    environment = {"os": platform.mac_ver()[0], "machine": platform.machine(), "python": platform.python_version(),
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "chrome": subprocess.check_output(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"], text=True).strip(),
        "toolVersions": json.loads((tooling / "package.json").read_text())["dependencies"],
        "viewport": [1440, 1000], "scaledViewport": [1024, 768], "deviceScaleFactor": 1,
        "workers": 1, "retries": 0, "reducedMotion": "reduce", "browserContexts": "fresh, headless; never user profiles",
        "source": "Pinned HEAD plus pre-existing dirty checkout; source_before.json checkpoint"}
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    write(HERE / "ENVIRONMENT.json", environment)
    decision = {"gate_id": "G2", "phase": "P03_DESIGN_SYSTEM", "status": "PASS", "date": "2026-10-08", "commit_sha": sha,
        "decision": "TESTED_OPT_IN_COMPONENT_FOUNDATION", "owner": "Frontend lead role; Codex implementation/evidence review",
        "humanUsabilityCertification": False, "nativeAssistiveTechnologyCertification": False,
        "components": 18, "browserChecks": 44, "javascriptTests": 57,
        "pythonTests": {"passed": totals["tests"]-totals["skipped"], "skipped": totals["skipped"]},
        "accessibilityAutomatedViolations": {"dark": 0, "highContrast": 0}, "productionShellMigrated": False,
        "existingScientificSourceChanged": False, "productionNativeIntegrationApproved": False,
        "architectureDeviations": [], "blockers": [], "next": "P04_APP_SHELL", "p04Executed": False,
        "deferredAcceptance": ["Real shell/state/job/review/export adapters and rollback in P04",
            "Native screen-reader, real-user and supported-platform acceptance", "Native geometry SBOM/packaging and later geometry gates"],
        "reports": ["P03_IMPLEMENTATION_REPORT.md", "P03_SCRIPTED_TASK_STUDIES.md", "P03_BUILD_AND_REPRODUCE.md"]}
    write(HERE / "G2_DECISION.json", decision)
    # Refresh only the explicitly approved P01 review record lineage, not historical test outcomes.
    approval_register = json.loads((P01 / "EVIDENCE_REGISTER.json").read_text())
    for claim in approval_register["claims"]:
        for artifact in claim.get("artifacts", []):
            artifact["sha256"] = digest(P01 / artifact["path"])
    approval_register["owner_acceptance"] = json.loads((P01 / "G1_DECISION.json").read_text())["human_acceptance"]
    approval_register["owner_acceptance_artifacts"] = [{"path": "approval/G1_PRE_APPROVAL.json",
        "sha256": digest(P01 / "approval/G1_PRE_APPROVAL.json")}, {"path": "G1_DECISION.json", "sha256": digest(P01 / "G1_DECISION.json")}]
    write(P01 / "EVIDENCE_REGISTER.json", approval_register)
    completion = P02 / "completion"
    for name in ("p02-completion-final.log", "p02-export-tests-final.log", "p02-independent-tests.log", "p02-raw-retest.log", "p02-retained-verify.log"):
        shutil.copy2(logs / name, completion / name)
    write(completion / "EVIDENCE_REGISTER.json", {"gate_id": "P02_FEASIBILITY", "requirement_ids": ["GOV-001", "GOV-002", "GOV-004", "GOV-005", "GOV-009", "GOV-010"],
        "commit_sha": sha, "date": "2026-10-08", "environment": environment, "reviewer": "Codex independent export re-audit",
        "decision": "PASS_ISOLATED_SOURCE_CANDIDATE_ONLY", "blockers": [],
        "commands": ["complete_feasibility.py source-built worker", "test_export_adapter.py: 6 passed", "test_mesh_audit.py: 10 passed",
            "run_benchmarks.py raw_retest: expected exit 1, 17/21 raw; 17/17 negatives", "finalize_completion.py --verify"],
        "test_artifacts": ["accepted_benchmarks.json", "raw_retest.json", "ARTIFACT_MANIFEST.json"],
        "notApproved": ["G5", "G6", "G9", "Production integration/redistribution", "CAD-ready or physical-validation claims"],
        "artifacts": artifacts([p for p in completion.rglob("*") if p.name != "EVIDENCE_REGISTER.json"] + [P02 / "P02_DECISION.json", P02 / "dependency_manifest.json", P02 / "P02_LICENSE_MATRIX.md"] )})
    # Re-run preservation after the final authorized record mutation.
    subprocess.run([sys.executable, str(HERE / "check_scope.py")], cwd=ROOT, check=True, capture_output=True)
    files = [p for p in HERE.rglob("*") if p.name != "EVIDENCE_REGISTER.json"]
    files += list((ROOT / "gui/static/design-system").rglob("*")) + list((ROOT / "tests/ui/design-system").rglob("*"))
    files += [ROOT / "tests/js/design_system.test.cjs", P01 / "G1_DECISION.json", P01 / "P01_REVIEW_RECORD.md", P01 / "EVIDENCE_REGISTER.json"]
    write(HERE / "EVIDENCE_REGISTER.json", {"gate_id": "G2", "requirement_ids": ["G2", "GOV-001", "GOV-002", "GOV-003", "GOV-004", "GOV-007", "GOV-009", "GOV-010", "specs/02_DESIGN_SYSTEM.md"],
        "commit_sha": sha, "environment": environment, "date": "2026-10-08", "reviewer": "Codex Frontend lead role; automated browser and source evidence",
        "decision": "PASS_TESTED_OPT_IN_FOUNDATION", "blockers": [], "commands": ["pytest --import-mode=importlib -q: 2234 passed, 5 skipped",
            "node --test tests/js/*.test.cjs: 57 passed", "Playwright configured regression: 44 passed", "Ruff repository and phase scopes: pass",
            "Mypy scientific/API scope: 318 files pass", "TypeScript strict public consumer contracts: pass", "build_tokens.py --check", "check_scope.py", "git diff --check"],
        "test_artifacts": ["browser-tests.json", "accessibility-dark.json", "accessibility-high-contrast.json", "screenshots/", "logs/", "source_integrity.json"],
        "artifacts": artifacts(files)})
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        assert args.tools and args.tools.is_dir(), "Supply the isolated test-tool directory"
        build(args.tools)
