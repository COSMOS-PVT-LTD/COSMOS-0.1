"""Seal executed P10 software proof, not physical or human engineering acceptance."""
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from api.ngg_workbench import runtime_config
from systems.contracts.geometry._wire import digest as wire_digest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEAL = HERE / "artifact_hashes.json"


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    target = HERE / name
    assert not target.exists(), f"Do not replace executed evidence: {name}"
    target.write_text(json.dumps(value, indent=2) + "\n")


def pytest_result(name):
    suites = list(ET.parse(HERE / name).getroot().iter("testsuite"))
    assert suites and all(int(s.attrib["failures"]) == int(s.attrib["errors"]) == 0 for s in suites)
    skipped = sum(int(s.attrib["skipped"]) for s in suites)
    return {"passed": sum(int(s.attrib["tests"]) for s in suites)-skipped, "skipped": skipped}


def preservation():
    baseline = read("baseline.json")
    expected_changed = {"gui/server.py", ".github/workflows/ci.yml"}
    changed = [name for name, expected in baseline["sha256"].items() if not (ROOT/name).is_file() or filehash(ROOT/name) != expected]
    assert set(changed) == expected_changed, changed
    for name in expected_changed:
        assert filehash(HERE/"before"/name) == baseline["sha256"][name], name
    assert filehash(ROOT/"cache/cea/test_key.json") == "6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508"
    save("source_integrity.json", {"pass": True, "baseline_files": len(baseline["sha256"]), "only_changed": changed,
        "unrelated_work_preserved": True, "synthetic_test_cache_exactly_restored": True, "baseline_commit_sha": baseline["commit_sha"]})
    predecessor = json.loads((HERE.parent/"P09_2026-10-10/artifact_hashes.json").read_text())
    for name, expected in predecessor.items():
        path = HERE/"before"/name if name in expected_changed else ROOT/name
        assert filehash(path) == expected, name
    save("predecessor_integrity.json", {"pass": True, "predecessor_files": len(predecessor),
        "before_overlay": sorted(expected_changed), "historical_seal_unmodified": True})


def checks():
    python = pytest_result("python-canonical.xml")
    focused = pytest_result("focused-canonical-final.xml")
    native = pytest_result("native-canonical.xml")
    assert python == {"passed": 2685, "skipped": 76}
    assert focused == {"passed": 48, "skipped": 0}
    assert native == {"passed": 4, "skipped": 0}
    assert pytest_result("baseline-tests.xml") == {"passed": 2637, "skipped": 72}
    browser = read("browser-tests.json")["stats"]
    assert browser["expected"] == 13 and browser["unexpected"] == browser["flaky"] == browser["skipped"] == 0
    javascript = (HERE/"javascript-canonical.log").read_text()
    assert re.search(r"pass 124\b", javascript) and re.search(r"fail 0\b", javascript)
    assert "All checks passed!" in (HERE/"ruff-canonical.log").read_text()
    assert "Success: no issues found in 344 source files" in (HERE/"mypy-canonical.log").read_text()
    assert not (HERE/"display-contracts-canonical.log").read_text().strip()
    for name in ("physics_parity.json", "refinement.json", "native-artifact-integrity-final5.json", "receipt-integrity.json"):
        assert read(name)["pass"], name
    assert read("physics_parity.json")["tolerance"] == 0
    for theme in ("dark", "high-contrast"):
        assert not read("accessibility-"+theme+".json")["violations"]
    for row in read("performance.json"):
        assert row["scrollWidth"] <= row["width"] and row["plotCount"] == 3
    for item in read("native-artifact-integrity-final5.json")["retained"]:
        assert filehash(ROOT/item["path"]) == item["sha256"]
    for name in ("analytic-assessment.json", "cross-kernel-assessment.json", "downloaded-receipt.json"):
        receipt = read(name)
        assert hashlib.sha256(receipt["canonical_json"].encode()).hexdigest() == receipt["report_id"]
        assert json.loads(receipt["canonical_json"]) == receipt["report"]
        assert receipt["report"]["production_handoff"] is receipt["report"]["independent_acceptance"] is False
        assert receipt["report"]["experimental_validation"] == "not-performed"
    thermal, geometry = read("analytic-assessment.json")["report"], read("cross-kernel-assessment.json")["report"]
    assert thermal["error_criteria_passed"] and thermal["combined_standard_uncertainty_k"] is None
    assert thermal["candidate"]["provenance"]["source_sha256"] == wire_digest(read("p09-current-dataset.json"))
    assert geometry["comparison_passed"] and geometry["cross_kernel"]
    imported = read("external-step-import.json")["result"]
    assert imported["qa"]["pass"] and imported["qa"]["reader_kernel_independence"] is False
    assert filehash(HERE/"native-artifacts-final5/external-step/import.step") == imported["source_sha256"]
    signoff = read("signoff-report.json")
    assert not signoff["signed_human_approval"] and signoff["production_handoff"] == "BLOCKED"
    return {"python": python, "p10_focused_included_in_python": focused, "actual_native": native,
        "javascript_passed": 124, "browser_passed": 13, "axe_violations": {"dark": 0, "high-contrast": 0},
        "physics_parity_cases": 5, "refinement_cases": 4, "ruff": "PASS", "mypy_files": 344,
        "strict_display_contracts": "PASS", "remote_ci_executed": False}


def main():
    runtime_config((HERE.parent/"P08_2026-10-09/local-runtime.json").resolve())
    if sys.argv[1:] == ["--verify"]:
        hashes = read("artifact_hashes.json")
        for name, expected in hashes.items():
            assert filehash(ROOT/name) == expected, name
        print(json.dumps({"evidence_integrity": "PASS", "sealed_files": len(hashes), "G8_software": "PASS",
            "production_handoff": False, "experimental_validation": False, "human_acceptance": False}))
        return
    assert not SEAL.exists(), "Do not replace sealed evidence; create a reproduction overlay"
    summary = checks()
    preservation()
    commands = [".venv-remediation/bin/python -m pytest -q", "COSMOS_P10_NATIVE=1 .venv-remediation/bin/python -m pytest tests/integration_tests/validation/test_native_comparison.py -q",
        "node --test tests/js/*.test.cjs", "NODE_PATH=/private/tmp/cosmos-p03.pfPm6s/node_modules node /private/tmp/cosmos-p03.pfPm6s/node_modules/@playwright/test/cli.js test --config=tests/ui/comparison/playwright.config.cjs",
        ".venv-remediation/bin/python -m ruff check core knowledge physics numerics systems simulation validation api gui infrastructure plugins tests tools",
        ".venv-remediation/bin/python -m mypy core physics numerics systems api simulation validation",
        "node /private/tmp/cosmos-p03.pfPm6s/node_modules/typescript/bin/tsc --noEmit --strict --target ES2020 --module Node16 --moduleResolution Node16 tests/ui/comparison/type_contracts.ts",
        "PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P10_2026-10-11/collect_evidence.py; then --retain for final native/receipt reproduction"]
    gate = {"gate_id": "G8_VV", "phase": "P10_COMPARISON_VV", "decision": "SOFTWARE_PASS", "software_pass": True,
        "date": "2026-10-11", "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "working_tree_evidence": "Dirty-tree baseline, two-file before overlay and artifact_hashes.json; not a published Git revision",
        "environment": "Local macOS arm64, CPython 3.11.4, actual Chrome, qualified OCCT/PicoGK/Gmsh",
        "scope": "Small fixed-fixture geometry and steady spherical thermal software comparison preview",
        "requirement_ids": ["GOV-001", "GOV-003", "GOV-004", "GOV-005", "GOV-007", "GOV-008", "GOV-009", "GOV-010", "G8"],
        "commands": commands, "tests": summary,
        "test_artifacts": ["python-canonical.xml", "native-canonical.xml", "javascript-canonical.log", "browser-tests.json", "refinement.json", "physics_parity.json", "native-artifact-integrity-final5.json", "receipt-integrity.json", "source_integrity.json", "predecessor_integrity.json", "signoff-report.json"],
        "reviewer": "Codex automated software assessment; not qualified independent engineering acceptance",
        "formal_human_acceptance": False, "experimental_validation": False, "production_handoff": False,
        "default_enabled": False, "engineering_publication": False,
        "blockers": {"scoped_software_gate": [], "physical_and_production": ["No compatible measured dataset secured or evaluated", "No qualified independent reviewer acceptance or full uncertainty budget", "G9 packaging, security, operational and remote CI release evidence pending"]},
        "limits": ["Output-only uncertainty, not full model/input UQ; unknown remains null", "Fixed geometry/thermal fixtures; no arbitrary CAD/CAE/engine qualification", "Ephemeral storage and preview review intent, not durable signed engineering records"],
        "next": "P11_KNOWLEDGE_REPORTS", "p11_readiness": "Research-tool evidence/reporting only", "p11_executed": False}
    save("test-summary.json", summary); save("G8_GATE.json", gate)
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    # Retained native bytes, logs and images may be ignored by repository-wide patterns.
    names += [str(p.relative_to(ROOT)) for p in HERE.rglob("*") if p.is_file()]
    hashes = {name: filehash(ROOT/name) for name in sorted(set(names)) if name and (ROOT/name).is_file() and ROOT/name != SEAL and "__pycache__" not in Path(name).parts}
    save("artifact_hashes.json", hashes)
    print(json.dumps({"G8_software": "PASS", "sealed_files": len(hashes), "tests": summary,
        "experimental_validation": False, "production_handoff": False}))


if __name__ == "__main__":
    main()
