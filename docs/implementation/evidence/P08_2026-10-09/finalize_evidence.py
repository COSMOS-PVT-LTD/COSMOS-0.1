"""Derive software gate from executed evidence and seal nonignored repository files.

--verify checks bytes/receipts only; it does not re-execute tests or grant human
engineering/product/native-release acceptance.
"""
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEAL = HERE / "artifact_hashes.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_result(name):
    suite = next(ET.parse(HERE / "logs" / name).getroot().iter("testsuite"))
    assert int(suite.attrib["failures"]) == int(suite.attrib["errors"]) == 0
    skipped = int(suite.attrib["skipped"])
    return {"passed": int(suite.attrib["tests"]) - skipped, "skipped": skipped}


def main():
    if sys.argv[1:] == ["--verify"]:
        hashes = json.loads(SEAL.read_text())
        for name, expected in hashes.items():
            assert digest(ROOT / name) == expected, name
        config = json.loads((HERE / "local-runtime.json").read_text())
        for name, expected in config["sha256"].items():
            assert digest(Path(name)) == expected, name
        assert digest(Path(config["g5_receipt"])) == config["g5_receipt_sha256"]
        print(json.dumps({"evidence_integrity": "PASS", "sealed_files": len(hashes), "G5_software": "PASS", "G6_software": "PASS",
                          "human_acceptance": False, "production_native": False}))
        return
    assert not SEAL.exists(), "Do not overwrite sealed acceptance; create a new reproduction overlay"
    python = test_result("pytest-final2.xml")
    native = test_result("native-final2.xml")
    assert python == {"passed": 2581, "skipped": 65} and native == {"passed": 58, "skipped": 0}
    browser = json.loads((HERE / "browser-tests.json").read_text())["stats"]
    assert browser["expected"] == 12 and browser["unexpected"] == browser["flaky"] == browser["skipped"] == 0
    js = (HERE / "logs/js-final2.log").read_text()
    assert re.search(r"pass 98\b", js) and re.search(r"fail 0\b", js)
    assert "All checks passed!" in (HERE / "logs/ruff-final3.log").read_text()
    assert "Success: no issues found in 332 source files" in (HERE / "logs/mypy-final2.log").read_text()
    assert not (HERE / "logs/types-final.log").read_text().strip()
    parity = json.loads((HERE / "physics_parity.json").read_text())
    assert parity["pass"] and parity["cases"] == 5 and parity["tolerance"] == 0
    preservation = json.loads((HERE / "source_integrity.json").read_text())
    assert preservation["pass"] and preservation["known_cea_timestamp_restored_exactly"] and preservation["e2e_exact_downloaded_bytes_retained"]
    reaudit = json.loads((HERE / "candidate-reaudit.json").read_text())
    assert reaudit["pass"] and reaudit["full_G5_pass"] and len(reaudit["records"]) == 30
    for theme in ("dark", "high-contrast"):
        assert not json.loads((HERE / f"accessibility-{theme}.json").read_text())["violations"]
    for backend in ("occt", "picogk"):
        result = json.loads((HERE / f"e2e-{backend}.json").read_text())
        assert result["status"]["state"] == "accepted" and result["reimport"]["result"]["pass"]
        assert not result["reimport"]["result"]["published"] and not result["reimport"]["result"]["physical_validation"]
        artifact = result["status"]["record"]["artifacts"][0]
        file = HERE / "exchanged-fixtures" / backend / Path(artifact["storage_uri"]).name
        assert digest(file) == artifact["sha256"] == result["reimport"]["result"]["artifact_sha256"]
        assert result["status"]["snapshot_id"] == result["context"]["snapshot"]["content_sha256"] == result["reimport"]["result"]["snapshot_id"]
    perf = json.loads((HERE / "viewport-performance.json").read_text())
    assert 100 < perf["triangleCount"] <= 200000 and perf["bufferBytes"] <= 7200000 and perf["loadMs"] < 1500
    summary = {"python": python, "actual_native": native, "javascript_passed": 98, "browser_passed": 12,
               "axe_violations": {"dark": 0, "high-contrast": 0}, "physics_parity_cases": 5,
               "ruff": "PASS", "mypy_files": 332, "strict_display_contracts": "PASS", "reaudited_records": 30,
               "viewport_measurement_scope": "Local Chrome CPU draw/load timings, not GPU/FPS or large-model certification",
               "physical_validation": False, "github_ci_run": False}
    gate = {"phase": "P08_NGG_WORKBENCH", "gate": "G6_NGG_UI", "status": "SOFTWARE_PASS", "software_pass": True,
            "prerequisite_g5_software": True, "default_enabled": False, "fixture_scope_only": True,
            "formal_ux_cad_owner_acceptance": False, "engineering_publication": False,
            "native_distribution_approved": False, "physical_validation": False,
            "next": "P09_SIMULATION", "p09_executed": False, "tests": summary}
    (HERE / "test-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (HERE / "G6_GATE.json").write_text(json.dumps(gate, indent=2) + "\n")
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    hashes = {name: digest(ROOT / name) for name in sorted(set(names))
              if name and (ROOT / name).is_file() and ROOT / name != SEAL}
    SEAL.write_text(json.dumps(hashes, indent=2) + "\n")
    print(json.dumps({"G5_software": "PASS", "G6_software": "PASS", "sealed_files": len(hashes), "human_acceptance": False}))


if __name__ == "__main__":
    main()
