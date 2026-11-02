"""Seal/verify a PARTIAL P07 handoff. Never turn failed geometry into a passed gate."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = str(HERE.relative_to(ROOT)) + "/"
CODE = ("infrastructure/geometry/", "plugins/geometry/", "systems/geometry/",
        "tests/unit_tests/infrastructure/test_geometry_", "tests/unit_tests/plugins/test_geometry_",
        "tests/unit_tests/systems_layer/test_ngg_", "tests/integration_tests/geometry/", "tests/contracts/ngg/", "tests/fixtures/ngg_")
LOGS = ("focused-final.log", "focused-final.xml", "pytest-final.log", "pytest-final.xml", "native-complete.log", "native-complete.xml",
        "native-guards-final.log", "native-guards-final.xml", "native-conformance.log", "native-conformance.xml", "js-final.log",
        "ruff-final.log", "mypy-final.log", "compile-final.log", "physics-parity.log", "reaudit.log", "diff-final.log",
        "cad-install.log", "cad-import-diagnostic.log", "cad-import-sample.log", "cad-import-sample.txt", "ocp-import-diagnostic.log",
        "gmsh-wheel-download.log", "gmsh-extract.log", "gmsh-mm-probe.log", "pico-first.log", "pico-patched.log",
        "pico-build-final.log", "patched-build.log", "probe-build.log", "occt-first.log", "occt-si.log", "step-qa-first.log", "config-final.log")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def scope():
    spec = importlib.util.spec_from_file_location("p07_scope", HERE / "check_scope.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = module.hashes()
    before = json.loads((HERE / "source_before.json").read_text())
    assert all(current.get(name) == sha for name, sha in before.items()), "Pre-existing file changed"
    assert all(name.startswith(module.ADDITIONS) for name in current if name not in before), "Out-of-scope addition"
    return len(before)


def predecessors():
    result = []
    for phase in ("P05_2026-10-09", "P06_2026-10-09"):
        manifest = HERE.parent / phase / "artifact_hashes.json"
        entries = json.loads(manifest.read_text())
        assert all(digest(ROOT / name) == sha for name, sha in entries.items()), phase
        result.append({"phase": phase, "pass": True, "sealed_entries": len(entries), "manifest_sha256": digest(manifest)})
    directory = HERE.parent / "P02_2026-10-08/completion"
    entries = json.loads((directory / "ARTIFACT_MANIFEST.json").read_text())
    assert all(digest(directory / entry["path"]) == entry["sha256"] for entry in entries)
    result.append({"phase": "P02 completion", "pass": True, "artifact_entries": len(entries), "manifest_sha256": digest(directory / "ARTIFACT_MANIFEST.json")})
    return result


def summary(name):
    cases = list(ET.parse(HERE / "logs" / name).getroot().iter("testcase"))
    failures = [c.attrib["name"] for c in cases if c.find("failure") is not None or c.find("error") is not None]
    skipped = sum(c.find("skipped") is not None for c in cases)
    return {"total": len(cases), "passed": len(cases) - len(failures) - skipped, "failed": len(failures), "skipped": skipped,
            "failures": failures}


def check():
    assert scope() == 1846
    predecessors()
    tests = {"python": summary("pytest-final.xml"), "focused": summary("focused-final.xml"),
             "native": summary("native-complete.xml"), "native_guards_replay": summary("native-guards-final.xml")}
    assert tests["python"]["passed"] == 2560 and tests["python"]["failed"] == 0 and tests["python"]["skipped"] == 59
    assert tests["focused"]["passed"] == 84 and tests["focused"]["failed"] == tests["focused"]["skipped"] == 0
    assert tests["native"]["passed"] == 50 and tests["native"]["failed"] == 4 and tests["native"]["skipped"] == 0
    assert set(tests["native"]["failures"]) == {
        "test_occt_step_independent_tool_reimport[union]", "test_occt_step_independent_tool_reimport[difference]",
        "test_occt_step_independent_tool_reimport[intersection]", "test_occt_step_and_stl_representation_aware_export"}
    assert tests["native_guards_replay"]["passed"] == 24 and tests["native_guards_replay"]["failed"] == tests["native_guards_replay"]["skipped"] == 0
    assert "pass 94" in (HERE / "logs/js-final.log").read_text() and "fail 0" in (HERE / "logs/js-final.log").read_text()
    assert (HERE / "logs/ruff-final.log").read_text().strip() == "All checks passed!"
    assert "Success: no issues found in 336 source files" in (HERE / "logs/mypy-final.log").read_text()
    assert not (HERE / "logs/compile-final.log").read_text() and not (HERE / "logs/diff-final.log").read_text()
    assert json.loads((HERE / "physics_parity.json").read_text())["pass"]
    reaudit = json.loads((HERE / "candidate-reaudit.json").read_text())
    assert reaudit["pass"] and len(reaudit["records"]) == 30 and not reaudit["full_G5_pass"]
    assert all(not row["published"] and not row["physical_validation"] for row in reaudit["records"])
    assert json.loads((HERE / "source_integrity.json").read_text())["existingChanges"] == []
    tests.update({"javascript_passed": 94, "ruff": "PASS", "mypy_source_files": 336, "python_compile": "PASS",
                  "physics_http_exact_cases": 5, "candidate_reaudit_records": 30, "golden_dotnet_vectors": 14,
                  "native_optional_skips_in_python_suite": 54, "existing_skips": 5})
    return tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        entries = json.loads((HERE / "artifact_hashes.json").read_text())
        assert all(digest(ROOT / name) == sha for name, sha in entries.items()), "Sealed artifact changed"
        check()
        gate = json.loads((HERE / "G5_GATE.json").read_text())
        assert gate["decision"] == "PARTIAL_G5_NOT_PASSED" and not gate["g5_pass"] and not gate["p08_ready"]
        print(json.dumps({"evidence_integrity": "PASS", "sealed_files": len(entries), "phase_status": "PARTIAL", "g5_pass": False, "p08_ready": False}))
        return
    assert args.scratch is not None and args.scratch.is_dir()
    for name in LOGS:
        source = args.scratch / name
        assert source.is_file(), name
        shutil.copyfile(source, HERE / "logs" / name)
    write("predecessor_integrity.json", {"pass": True, "entries": predecessors()})
    tests = check()
    write("test-summary.json", tests)
    runtime = json.loads((HERE / "native-runtime-manifest.json").read_text())
    write("G5_GATE.json", {"gate_id": "G5", "phase": "P07_NGG_KERNELS", "requirement_ids": ["P07.Execute", "G5.KernelFixtures", "G5.TopologyQA", "G5.ExportRoundTrip"],
        "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(), "dirty_checkout": True,
        "environment": {"platform": runtime["platform"], "python": runtime["python"], "native_manifest": "native-runtime-manifest.json"},
        "commands": ["python -m pytest -q", "P07_NATIVE_CONFIG=<explicit-hash-checked-config> python -m pytest -q tests/integration_tests/geometry", "node --test tests/js/*.test.cjs",
                     "python -m ruff check <established-whole-source-scope>", "python -m mypy core physics numerics systems api infrastructure/geometry plugins/geometry",
                     "python verify_physics.py", "python reaudit_candidates.py"],
        "test_artifacts": ["test-summary.json", "candidate-reaudit.json", "logs/native-complete.xml", "runs/final3/fixtures", "physics_parity.json", "source_integrity.json", "predecessor_integrity.json"],
        "reviewer": "Codex local software evidence; no independent CAD-lead/physical/release signoff", "decision": "PARTIAL_G5_NOT_PASSED",
        "date": datetime.now(timezone.utc).isoformat(), "blockers": tests["native"]["failures"], "tests": tests,
        "implemented": ["bounded POSIX supervisor", "default-disabled PicoGK and direct OCCT adapters", "P06 immutable typed candidates",
                        "independent mesh QA and STEP-tool reimport", "explicit representation-aware candidate export", "native fixture and .NET transport conformance"],
        "g5_pass": False, "p08_ready": False, "production_native_activation": False, "published_artifacts": 0,
        "physical_validation_claimed": False, "native_distribution_approved": False, "existing_source_changes": [], "next": "P08_NGG_WORKBENCH — withheld until G5 closure"})
    files = [p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name != "artifact_hashes.json"]
    names = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    files += [ROOT / name for name in sorted(set(names)) if name.startswith(CODE) and (ROOT / name).is_file()]
    write("artifact_hashes.json", {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files))})
    print(json.dumps({"sealed_files": len(set(files)), "phase_status": "PARTIAL", "g5_pass": False, "native_passed": 50, "native_failed": 4}))


if __name__ == "__main__":
    main()
