"""Retain and independently re-audit P02 completion; never alter original raw evidence."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P02 = HERE.parent
sys.path.insert(0, str(P02))
from run_benchmarks import audit_mesh


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    result = json.loads((HERE / "accepted_benchmarks.json").read_text())
    assert result["allPass"] and len(result["cases"]) == 21 and not result["tolerancesChanged"]
    raw = json.loads((HERE / "raw_retest.json").read_text())
    assert not raw["allPass"] and sum(case["pass"] for case in raw["cases"]) == 17
    assert len(raw["negativeCases"]) == 17 and all(case["pass"] for case in raw["negativeCases"])
    assert raw["lifecycle"]["pass"] and raw["cancellation"]["pass"]
    assert all(group["pass"] for group in raw["convergence"].values())
    for case in result["cases"]:
        assert case["pass"]
        for attempt in case["attempts"]:
            assert 0 < attempt["run"]["maximumResidentBytes"] < 1073741824
            cycle = attempt["run"]["events"][-1]["cycles"][0]
            assert cycle["nativeBytesAfter"] == cycle["nativeAllocationsAfter"] == 0
    manifest = json.loads((HERE / "ARTIFACT_MANIFEST.json").read_text())
    for item in manifest:
        artifact = HERE / item["path"]
        assert digest(artifact) == item["sha256"]
        if item["role"] == "conditioned":
            qa = audit_mesh(artifact, item["operation"], .01, .01, item["actualVoxelM"])
            assert qa["pass"] == item["expectedQaPass"]
    print(json.dumps({"candidate": "21/21", "raw": "17/21 known failures preserved", "negatives": "17/17",
        "artifactHashes": len(manifest), "independentRetainedExportReaudit": "PASS"}))


def retain():
    result = json.loads((HERE / "accepted_benchmarks.json").read_text())
    artifacts = []
    target_root = HERE / "artifacts"
    target_root.mkdir(exist_ok=True)
    for case in result["cases"]:
        for index, attempt in enumerate(case["attempts"]):
            if not attempt.get("conditioning"):
                continue
            operation, requested = case["request"]["operation"], case["request"]["voxelM"]
            source = Path(attempt["run"]["events"][-1]["cycles"][0]["path"])
            for role, path in (("raw", source), ("conditioned", source.parent / "conditioned.stl")):
                target = target_root / f"{operation}-{requested:.6f}m-attempt{index}-{role}.stl"
                if target.exists():
                    assert digest(target) == digest(path)
                else:
                    shutil.copy2(path, target)
                expected = attempt["conditioning"]["sourceSha256" if role == "raw" else "exportSha256"]
                assert digest(target) == expected
                artifacts.append({"path": str(target.relative_to(HERE)), "sha256": expected,
                    "operation": operation, "requestedVoxelM": requested, "actualVoxelM": attempt["actualVoxelM"],
                    "attempt": index, "role": role, "expectedQaPass": attempt["qa"]["pass"], "cadReady": False})
    (HERE / "ARTIFACT_MANIFEST.json").write_text(json.dumps(artifacts, indent=2) + "\n")
    verify()
    decision = json.loads((P02 / "P02_DECISION.json").read_text())
    decision.update(status="PASS", phasePassed=True, decision="ISOLATED_SOURCE_WORKER_CONDITIONED_EXPORTS_FEASIBLE",
        p01OwnerApproval="ACCEPTED_BY_OWNER", p03Started=True, blockers=[],
        acceptedCandidate={"passed": 21, "total": 21, "attempts": 22, "refined": 1, "tolerancesChanged": False,
            "profile": result["profile"]},
        scope="Isolated local source-built worker and explicit conditioned exploratory STL; not production integration or distribution",
        deferredReleaseGates=["Native/source/asset notice and SBOM closure", "Relocation, supported platforms, signing and notarization",
            "P06/P07 contracts, independent production geometry acceptance and integration"],
        knownRawDefects=["22 exact-zero-area subtraction faces at each tested resolution", "Unrefined 1 mm intersection exceeds dimensional ceiling"],
        nextPhaseCondition="P01 accepted by owner; P03 has independent evidence; no production native approval inferred")
    for path in ["completion/P02_COMPLETION_REPORT.md", "completion/accepted_benchmarks.json",
        "completion/raw_retest.json", "completion/ARTIFACT_MANIFEST.json", "completion/EVIDENCE_REGISTER.json"]:
        if path not in decision["evidence"]:
            decision["evidence"].append(path)
    (P02 / "P02_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    verify() if args.verify else retain()
