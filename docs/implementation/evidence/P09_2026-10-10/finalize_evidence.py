"""Seal executed P09 software evidence; verification never grants human signoff."""
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from api.ngg_workbench import runtime_config

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEAL = HERE / "artifact_hashes.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def pytest_result(name):
    suite = next(ET.parse(HERE / name).getroot().iter("testsuite"))
    assert int(suite.attrib["failures"]) == int(suite.attrib["errors"]) == 0
    skipped = int(suite.attrib["skipped"])
    return {"passed": int(suite.attrib["tests"]) - skipped, "skipped": skipped}


def main():
    config = (HERE.parent / "P08_2026-10-09/local-runtime.json").resolve()
    runtime_config(config)  # Real qualified native/source hashes and G5 receipt.
    if sys.argv[1:] == ["--verify"]:
        hashes = read("artifact_hashes.json")
        for name, expected in hashes.items():
            assert digest(ROOT / name) == expected, name
        print(json.dumps({"evidence_integrity": "PASS", "sealed_files": len(hashes), "G7_software": "PASS",
                          "production_handoff": False, "experimental_validation": False, "human_acceptance": False}))
        return
    assert not SEAL.exists(), "Do not overwrite a sealed gate; create a reproduction overlay"
    python, native = pytest_result("pytest-final3.xml"), pytest_result("native-final.xml")
    assert python == {"passed": 2637, "skipped": 72} and native == {"passed": 7, "skipped": 0}
    browser = read("browser-tests.json")["stats"]
    assert browser["expected"] == 10 and browser["unexpected"] == browser["flaky"] == browser["skipped"] == 0
    js = (HERE / "javascript-final.log").read_text()
    assert re.search(r"pass 114\b", js) and re.search(r"fail 0\b", js)
    assert "All checks passed!" in (HERE / "ruff-final.log").read_text()
    assert "Success: no issues found in 338 source files" in (HERE / "mypy-final.log").read_text()
    assert not (HERE / "type-contracts-final.log").read_text().strip()
    for name in ("source_integrity.json", "predecessor_integrity.json", "physics_parity.json", "refinement.json", "handoff-integrity.json"):
        assert read(name)["pass"], name
    assert read("physics_parity.json")["tolerance"] == 0
    for theme in ("dark", "high-contrast"):
        assert not read("accessibility-" + theme + ".json")["violations"]
    good = read("study-fixture.json")["run"]["result"]
    bad = read("nonconverged-fixture.json")["result"]
    assert good["numerical_convergence"] == "converged" and good["conservation_checks"]["passed"] and good["solution_verification"] == "analytic-benchmark-passed"
    assert bad["numerical_convergence"] == "nonconverged" and not bad["conservation_checks"]["passed"] and bad["solution_verification"] == "not-accepted"
    assert good["experimental_validation"] == bad["experimental_validation"] == "not-performed"
    assert good["production_handoff"] is bad["production_handoff"] is False
    for measurement in read("plot-performance.json"):
        assert measurement["scrollWidth"] <= measurement["width"] and measurement["plotCount"] == 4
    summary = {"python": python, "actual_native_handoff": native, "javascript_passed": 114, "browser_passed": 10,
               "axe_violations": {"dark": 0, "high-contrast": 0}, "physics_parity_cases": 5,
               "analytic_refinement_cases": 4, "ruff": "PASS", "mypy_files": 338, "strict_display_contracts": "PASS",
               "remote_ci_executed": False}
    gate = {"gate_id": "G7_SIMULATION", "phase": "P09_SIMULATION", "decision": "SOFTWARE_PASS", "software_pass": True,
            "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "date": "2026-10-10", "environment": "Local macOS arm64, CPython 3.11.4, actual Chrome, qualified OCCT/Gmsh",
            "scope": "steady-spherical-conduction-software-benchmark-only", "default_enabled": False,
            "requirement_ids": ["GOV-001", "GOV-003", "GOV-004", "GOV-007", "GOV-008", "GOV-009", "GOV-010", "T-011", "T-012", "T-013", "T-015"],
            "GOV-005_production_handoff": "BLOCKED_UNTIL_INDEPENDENT_ENGINEERING_ACCEPTANCE",
            "reviewer": "Codex automated software assessment; not independent engineering or UX owner signoff",
            "formal_human_acceptance": False, "engineering_publication": False, "production_handoff": False,
            "experimental_validation": False, "tests": summary, "next": "P10_COMPARISON_VV", "p10_executed": False,
            "remaining_boundaries": ["General 3D meshing/CFD/FEA/field maps and durable engineering storage not implemented",
                                     "Independent engineering signoff and production handoff unavailable",
                                     "Native distribution/packaging, security, other-platform and remote CI release gates pending"]}
    (HERE / "test-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (HERE / "G7_GATE.json").write_text(json.dumps(gate, indent=2) + "\n")
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    hashes = {name: digest(ROOT / name) for name in sorted(set(names)) if name and (ROOT / name).is_file() and ROOT / name != SEAL}
    SEAL.write_text(json.dumps(hashes, indent=2) + "\n")
    print(json.dumps({"G7_software": "PASS", "sealed_files": len(hashes), "tests": summary, "production_handoff": False}))


if __name__ == "__main__":
    main()
