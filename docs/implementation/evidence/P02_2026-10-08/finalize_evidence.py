"""Check phase evidence consistency and hash the deliverable tree, not a passing gate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def finalize():
    manifest = json.loads((HERE / "dependency_manifest.json").read_text())
    integrity = json.loads((HERE / "source_integrity.json").read_text())
    decision = json.loads((HERE / "P02_DECISION.json").read_text())
    assert integrity["pass"] and integrity["preexisting_files"] == 1546
    assert decision["status"] == "PARTIAL" and not decision["phasePassed"]
    assert len(manifest["sourcePins"]) == 7 and manifest["sdk"]["checksumVerified"]
    assert len(manifest["nativeArtifacts"]) == 12
    expected_failures = {("difference", .001), ("difference", .0005),
        ("difference", .00025), ("intersection", .001)}
    suites = []
    for name in ("prebuilt_benchmarks.json", "source_benchmarks.json"):
        data = json.loads((HERE / name).read_text())
        assert len(data["cases"]) == 21 and not data["allPass"]
        assert {(c["request"]["operation"], c["request"]["voxelM"])
            for c in data["cases"] if not c["pass"]} == expected_failures
        assert len(data["negativeCases"]) == 17 and all(c["pass"] for c in data["negativeCases"])
        assert data["lifecycle"]["pass"] and data["cancellation"]["pass"]
        assert all(c["pass"] for c in data["convergence"].values())
        suites.append({"file": name, "fixturePass": 17, "fixtureTotal": 21, "negativePass": 17})
    artifacts = json.loads((HERE / "artifacts/manifest.json").read_text())
    assert len(artifacts) == 5
    for artifact in artifacts:
        assert artifact["status"] == "UNVERIFIED"
        assert hashlib.sha256((HERE / artifact["persistedPath"]).read_bytes()).hexdigest() == artifact["sha256"]
    for entry in json.loads((HERE / "collected_evidence.json").read_text()):
        assert hashlib.sha256((HERE / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    files = [{"path": str(path.relative_to(HERE)), "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(HERE.rglob("*")) if path.is_file()
        and "__pycache__" not in path.parts and "obj" not in path.parts and "bin" not in path.parts
        and path.name != "EVIDENCE_REGISTER.json"]
    result = {"phase": "P02_PICOGK_FEASIBILITY", "status": "PARTIAL",
        "evidenceConsistency": "PASS", "notAGeometryGatePass": True,
        "sourcePreserved": True, "suites": suites, "files": files}
    (HERE / "EVIDENCE_REGISTER.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"evidenceConsistency": "PASS", "filesHashed": len(files),
        "phaseStatus": "PARTIAL", "sourcePreserved": True}))


if __name__ == "__main__":
    finalize()
