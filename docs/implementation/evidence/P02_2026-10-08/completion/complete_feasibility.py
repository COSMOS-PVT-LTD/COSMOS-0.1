"""Retest the source-built candidate with explicit conditioning and bounded refinement."""
import argparse
import json
import sys
from pathlib import Path

from export_adapter import condition

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from run_benchmarks import audit_mesh, invoke, request


def execute(dotnet, worker, output):
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    for h in (.001, .0005, .00025):
        for operation in ("sphere", "union", "difference", "intersection", "self_union", "self_difference", "disjoint_intersection"):
            original = request(operation, h)
            attempts = []
            for level in range(2):
                active = {**original, "voxelM": h / 2**level}
                root = output / f"{operation}-{h}-{level}"
                result = invoke(dotnet, worker, root, json.dumps(active))
                assert result["exitCode"] == 0
                assert result["maximumResidentBytes"] is not None and result["maximumResidentBytes"] < 1073741824
                assert [event["type"] for event in result["events"]] == ["started", "completed"]
                assert all(event["correlationId"] == active["correlationId"] for event in result["events"])
                final = result["events"][-1]["cycles"][0]
                assert final["nativeBytesAfter"] == 0 and final["nativeAllocationsAfter"] == 0
                if final["empty"]:
                    assert operation in ("self_difference", "disjoint_intersection")
                    attempts.append({"actualVoxelM": active["voxelM"], "run": result, "acceptedEmpty": True})
                    passed = True
                    break
                target = root / "conditioned.stl"
                transformation = condition(final["path"], target)
                qa = audit_mesh(target, operation, .01, .01, active["voxelM"])
                attempts.append({"actualVoxelM": active["voxelM"], "run": result, "conditioning": transformation, "qa": qa})
                passed = qa["pass"]
                if passed:
                    break
                # Only the diagnosed coarse intersection's dimensional failure permits refinement.
                assert operation == "intersection" and h == .001 and level == 0
                assert qa["degenerateFaces"] == qa["nonmanifoldEdges"] == qa["nonfiniteNormals"] == 0
                attempts[-1]["diagnostic"] = {"code": "RESOLUTION_REFINEMENT_REQUIRED", "requestedVoxelM": h,
                    "nextVoxelM": h / 2, "reason": "Original dimensional ceiling not met; tolerance unchanged"}
            cases.append({"request": original, "pass": passed, "attempts": attempts,
                "refined": len(attempts) > 1, "cadReady": False})
    result = {"profile": "source-native-conditioned-explicit-refinement-v1", "cases": cases,
        "allPass": all(c["pass"] for c in cases), "originalRawFailuresPreserved": True,
        "refinementBound": 1, "tolerancesChanged": False, "productionIntegrationApproved": False}
    (HERE / "accepted_benchmarks.json").write_text(json.dumps(result, indent=2) + "\n")
    assert result["allPass"]
    print(json.dumps({"fixturesPassed": len(cases), "total": len(cases), "refined": sum(c["refined"] for c in cases)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--worker", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute(args.dotnet, args.worker, args.output)
