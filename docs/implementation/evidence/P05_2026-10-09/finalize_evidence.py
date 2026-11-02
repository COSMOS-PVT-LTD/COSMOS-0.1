"""Seal/recheck executed P05 evidence. Verification does not rerun tests."""
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRODUCTION = ["gui/app_shell.py", "gui/server.py", "gui/static/app-shell/shell.js", "gui/static/propulsion-suite.js"]
LOGS = ["pytest-final.log", "pytest-final.xml", "python-focused.log", "js-final.log", "browser-final.log", "p04-compatibility.log", "ruff-final.log", "mypy-final.log", "types-final.log", "compile-final.log", "parity-after.log", "p03-retained.log"]


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def predecessor():
    entries = json.loads((HERE.parent / "P04_2026-10-09/artifact_hashes.json").read_text())
    before = json.loads((HERE / "source_before.json").read_text())
    for name, expected in entries.items():
        if name in PRODUCTION:
            assert before[name] == expected, name
        else:
            assert digest(ROOT / name) == expected, name
    return {"gate": "G3", "preP05Status": "PASS", "sealedEntries": len(entries), "retainedHistoricalEvidence": "PASS", "supersededProductionHashes": PRODUCTION, "note": "P04 scope/source hashes are historical; ignored retained logs verified against the predecessor seal"}


def check():
    subprocess.run([sys.executable, str(HERE / "check_scope.py")], cwd=ROOT, check=True, capture_output=True)
    integrity = json.loads((HERE / "source_integrity.json").read_text())
    assert integrity["pass"] and not integrity["scientificSourceChanged"]
    predecessor()
    parity = json.loads((HERE / "physics_parity.json").read_text())
    assert parity["pass"] and parity["numericalTolerance"] == 0
    assert json.loads((HERE / "physics_before.json").read_text()) == json.loads((HERE / "physics_after.json").read_text())
    assert parity["baselineSHA256"] == digest(HERE / "physics_before.json")
    for theme in ("dark", "high-contrast"):
        assert not json.loads((HERE / f"accessibility-{theme}.json").read_text())["violations"]
    metrics = json.loads((HERE / "interaction-metrics.json").read_text())
    assert metrics["p95Ms"] < 100 and metrics["inspectorMutations"] == 0
    for name in ("browser-tests.json", "p04-compatibility-tests.json"):
        stats = json.loads((HERE / name).read_text())["stats"]
        assert stats["unexpected"] == 0 and stats["flaky"] == 0 and stats["expected"] == 26, name
    suite = ET.parse(HERE / "logs/pytest-final.xml").getroot().find("testsuite")
    assert int(suite.attrib["tests"]) == 2277 and int(suite.attrib["skipped"]) == 5
    assert int(suite.attrib["errors"]) == int(suite.attrib["failures"]) == 0
    assert "pass 94" in (HERE / "logs/js-final.log").read_text()
    assert "fail 0" in (HERE / "logs/js-final.log").read_text()
    assert "All checks passed" in (HERE / "logs/ruff-final.log").read_text()
    assert "Success: no issues found in 318 source files" in (HERE / "logs/mypy-final.log").read_text()
    assert not (HERE / "logs/types-final.log").read_text().strip()
    assert not (HERE / "logs/compile-final.log").read_text().strip()
    assert '"evidenceHashes": "PASS"' in (HERE / "logs/p03-retained.log").read_text()
    for when in ("before", "after"):
        for stage in ("requirements", "thermochemistry", "cooling"):
            assert (HERE / f"{when}-{stage}.png").stat().st_size > 1000
    return integrity, metrics


def build(output):
    (HERE / "logs").mkdir(exist_ok=True)
    for name in LOGS:
        shutil.copy2(output / name, HERE / "logs" / name)
    integrity, metrics = check()
    write("predecessor_integrity.json", predecessor())
    write("G4_GATE.json", {"gate_id": "G4", "phase": "P05_ROCKET_ENGINE", "owner_role": "Scientific lead", "reviewer": "Codex executed local software evidence; not external physical validation", "status": "PASS", "decision": "PASS_TESTED_PRESENTATION_SLICE_DEFAULT_OFF", "sealed_at_utc": datetime.now(timezone.utc).isoformat(), "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "dirty_checkout": True, "scientific_source_changed": False, "physics_parity": {"actual_http_cases": 5, "comparison": "exact", "numerical_tolerance": 0}, "tests": {"python_passed": 2272, "python_skipped": 5, "javascript_passed": 94, "p05_browser_passed": 26, "p04_browser_compatibility_passed": 26, "axe_violations_dark": 0, "axe_violations_high_contrast": 0, "ruff": "PASS", "mypy_sources": 318, "typescript": "PASS", "gui_compilation": "PASS"}, "interaction": metrics, "default_off": True, "physical_validation_claimed": False, "sensitivity_service_added": False, "native_geometry_activated": False, "publishing_performed": False, "production_changes": integrity["existingChanges"], "next": "P06_NGG_CONTRACTS; not started"})
    files = [p for p in HERE.rglob("*") if p.is_file() and p.name != "artifact_hashes.json" and "__pycache__" not in p.parts]
    files += [ROOT / p for p in PRODUCTION]
    files += list((ROOT / "gui/static/rocket-workbench").glob("*"))
    files += [ROOT / "tests/js/rocket_workbench.test.cjs", ROOT / "tests/unit_tests/gui/test_rocket_workbench.py"]
    files += [p for p in (ROOT / "tests/ui/rocket-workbench").glob("*") if p.is_file()]
    write("artifact_hashes.json", {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files)) if p.is_file()})
    verify()


def verify():
    check()
    gate = json.loads((HERE / "G4_GATE.json").read_text())
    assert gate["status"] == "PASS" and not gate["scientific_source_changed"]
    entries = json.loads((HERE / "artifact_hashes.json").read_text())
    for name, expected in entries.items():
        assert digest(ROOT / name) == expected, name
    print(json.dumps({"gate": "G4", "status": "PASS", "hashes": len(entries), "pythonPassed": 2272, "javascriptPassed": 94, "browserPassed": 52, "physicsCasesExact": 5, "scientificSourceChanges": 0, "historicalP04Evidence": "retained", "defaultOff": True}))


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify"]:
        verify()
    else:
        build(Path(sys.argv[1]))
