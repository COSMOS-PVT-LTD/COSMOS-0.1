"""Execute independent refinement/parity checks and retain exact native bytes."""
import hashlib
import importlib.util
import json
import resource
import sys
import time
import urllib.request
from http import cookiejar
from itertools import pairwise
from pathlib import Path

from numerics.finite_volume.radial_diffusion import solve
from plugins.geometry.protocol import checked_file
from systems.contracts.geometry._wire import digest
from validation.benchmarks import analytic
from validation.comparison import compare
from validation.contracts import Criteria, MODEL, ThermalDataset

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STATE = Path("/tmp/cosmos-p10-preview.RYAlkz/after-final5")
BASE = "http://127.0.0.1:8821"


def save(name, data):
    target = HERE / name
    assert not target.exists(), f"Do not overwrite executed evidence: {name}"
    target.write_text(json.dumps(data, indent=2) + "\n")


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_scientific():
    assert not (HERE / "artifact_hashes.json").exists(), "Evidence already sealed"
    tick = time.perf_counter(); cases = []
    for cells in (8, 16, 32, 64):
        start = time.perf_counter()
        result = solve(.01, cells, 10, 1e6, 300, tolerance=1e-10, max_iterations=50000)
        d = ThermalDataset.parse({"schema_version": "p10-thermal-v1", "kind": "external-solver", "quantity": "Temperature", "coordinate_unit": "m", "value_unit": "K", "frame_id": "world", "model_id": MODEL,
            "conditions": {"radius_m": .01, "conductivity_w_m_k": 10., "generation_w_m3": 1e6, "surface_k": 300.},
            "coordinates": [float(v) for v in result.centers], "values": [float(v) for v in result.values], "standard_uncertainty_k": None,
            "provenance": {"source": "numerics/finite_volume/radial_diffusion.py", "author": "COSMOS actual numerical refinement fixture", "version": f"p10-cells-{cells}",
                "source_sha256": filehash(ROOT / "numerics/finite_volume/radial_diffusion.py"), "license": "repository license",
                "method": "Actual isolated radial solver; synthetic constant material/boundaries; not a measured experiment", "calibration_usage": "not-applicable", "uncertainty_basis": "unknown", "instrumentation": "not-applicable"}})
        bound = 1e6*.01**2/(6*10*cells**2)
        policy = Criteria.parse({"intended_use": "Independent spherical code/solution verification only", "rationale": "Predeclared P09 analytic discretization ceiling qR²/(6kN²), not a physical acceptance tolerance",
            "max_abs_error_k": bound, "max_combined_standard_uncertainty_k": bound, "coverage_factor": 2., "correlation": 0., "allow_unit_conversion": False})
        report = compare(d, analytic(d), policy)
        assert result.converged and report["error_criteria_passed"] and report["experimental_validation"] == "not-performed"
        assert abs(result.outward-result.generated)/result.generated <= 2*(cells**.5)*1e-10
        cases.append({"cells": cells, "report": report, "criteria": policy.data, "iterations": result.iterations[-1],
                      "normalized_residual": result.residual_history[-1], "signed_imbalance_w": result.outward-result.generated,
                      "elapsed_s": time.perf_counter()-start})
    ratios = [a["report"]["metrics"]["max_abs_error_k"]/b["report"]["metrics"]["max_abs_error_k"] for a, b in pairwise(cases)]
    assert all(3.9 < value < 4.1 for value in ratios)
    save("refinement.json", {"pass": True, "cases": cases, "error_ratios": ratios, "experimental_validation": False})
    save("numerical-performance.json", {"elapsed_s": time.perf_counter()-tick, "process_cumulative_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "macOS Python process cumulative RSS; not whole app/native/Chrome peak or per-run allocation"})
    spec = importlib.util.spec_from_file_location("p05_parity", HERE.parent / "P05_2026-10-09/physics_parity.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = module.run(); baseline = HERE.parent / "P09_2026-10-10/physics_after.json"
    assert current == json.loads(baseline.read_text())
    save("physics_after.json", current)
    save("physics_parity.json", {"pass": True, "cases": 5, "tolerance": 0, "baseline_sha256": filehash(baseline), "physical_validation": False})


def retain_native():
    assert not (HERE / "artifact_hashes.json").exists(), "Evidence already sealed"
    assert json.loads((HERE / "refinement.json").read_text())["pass"] and json.loads((HERE / "physics_parity.json").read_text())["pass"]
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    client.open(urllib.request.Request(BASE + "/api/auth/login", json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"}).encode(), {"Content-Type": "application/json"})).close()
    def get(path):
        with client.open(BASE+path) as response:
            return json.load(response)
    captures = json.loads((HERE / "cross-kernel-assessment.json").read_text())["report"]
    native = HERE / "native-artifacts-final5"; native.mkdir(exist_ok=True)
    records = []; checks = []
    for job in get("/api/ngg/context")["job_ids"]:
        status = get("/api/ngg/jobs/" + job)
        artifact = status["record"]["artifacts"][0]
        matching = next(v for v in (captures["left"], captures["right"]) if v["source_sha256"] == artifact["sha256"])
        assert matching["snapshot_id"] == status["snapshot_id"] == status["record"]["snapshot"]["content_sha256"]
        candidate = STATE / "ngg_software_candidates" / job
        directory = native / artifact["backend_id"]; directory.mkdir()
        source_name = "source.brep" if artifact["backend_id"] == "occt" else "source.vdb"
        for name, expected in ((Path(artifact["storage_uri"]).name, artifact["sha256"]), (source_name, artifact["source_artifact_sha256"])):
            original = checked_file(candidate, name, expected)
            with (directory / name).open("xb") as stream:
                stream.write(original.read_bytes())
            assert filehash(directory / name) == expected
            checks.append({"path": str((directory / name).relative_to(ROOT)), "sha256": expected})
        (directory / "status.json").write_text(json.dumps(status, indent=2)+"\n")
        records.append(status)
    assert len(records) == 2
    save("native-artifact-integrity-final5.json", {"pass": True, "records": len(records), "retained": checks, "cross_kernel": captures["cross_kernel"]})
    imported = json.loads((HERE / "external-step-import.json").read_text())["result"]
    matches = [p for p in STATE.glob("p10-trusted-step-*/import.step") if filehash(p) == imported["source_sha256"]]
    assert len(matches) == 1
    external = native / "external-step"; external.mkdir()
    with (external / "import.step").open("xb") as stream:
        stream.write(matches[0].read_bytes())
    assert filehash(external / "import.step") == imported["source_sha256"]
    receipt = json.loads((HERE / "analytic-assessment.json").read_text())
    assert hashlib.sha256(receipt["canonical_json"].encode()).hexdigest() == receipt["report_id"]
    assert json.loads(receipt["canonical_json"]) == receipt["report"]
    source = get("/api/simulation/runs/" + receipt["report"]["source_run_id"] + "/dataset")
    save("p09-current-dataset.json", source)
    assert receipt["report"]["candidate"]["provenance"]["source_sha256"] == digest(source)
    save("receipt-integrity.json", {"pass": True, "receipt_sha256": receipt["report_id"], "current_p09_dataset_bound": True})
    reviewed = get("/api/comparison/reports/" + receipt["report_id"])
    assert len(reviewed["review_intents"]) == 1 and reviewed["review_intents"][0]["independent_acceptance"] is False
    save("signoff-report.json", {"decision": "SOFTWARE_EVIDENCE_RECORDED_ONLY", "independent_engineering_acceptance": "PENDING",
        "reviewer_identity": "No qualified independent human reviewer appointed in this execution", "preview_review_intents": reviewed["review_intents"],
        "experimental_validation": "NOT_PERFORMED", "production_handoff": "BLOCKED", "signed_human_approval": False})
    print(json.dumps({"refinement_cases": 4, "physics_parity_cases": 5, "retained_native_kernels": 2, "experimental_validation": False}))


if __name__ == "__main__":
    if sys.argv[1:] != ["--retain"]:
        collect_scientific()
    retain_native()
