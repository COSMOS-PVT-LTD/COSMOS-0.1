"""Retain actual browser/native report proof and verify provenance/package bytes."""
import hashlib
import importlib.util
import io
import json
import resource
import time
import urllib.request
import zipfile
from http import cookiejar
from pathlib import Path

from plugins.geometry.protocol import checked_file
from systems.contracts.geometry._wire import digest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STATE = Path("/tmp/cosmos-p11-preview.1mQrjl/after-final2")
BASE = "http://127.0.0.1:8831"


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    target = HERE/name; assert not target.exists(), "Do not replace executed evidence: "+name
    target.write_text(json.dumps(value, indent=2)+"\n")


def main():
    tick = time.perf_counter()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    client.open(urllib.request.Request(BASE+"/api/auth/login", json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"}).encode(), {"Content-Type": "application/json"})).close()
    def get(path):
        with client.open(BASE+path) as response: return json.load(response)
    receipt = json.loads((HERE/"report-fixture.json").read_text()); report = receipt["report"]; key = receipt["report_id"]
    live = get("/api/knowledge-reports/reports/"+key)
    assert live["freshness"] == "current" and live["canonical_json"] == receipt["canonical_json"]
    assert hashlib.sha256(receipt["canonical_json"].encode()).hexdigest() == key
    assert json.loads(receipt["canonical_json"]) == report
    for record in report["claims"]:
        assert hashlib.sha256(record["canonical_json"].encode()).hexdigest() == record["evidence_sha256"]
        assert json.loads(record["canonical_json"]) == record["claim"]
        assert record["claim"]["source"]["source_origin"] == "synthetic-contract-fixture"
        original = STATE/"p11-synthetic-source-original.txt"
        assert filehash(original) == record["claim"]["source"]["sha256"]
        with (HERE/"synthetic-source-original.txt").open("xb") as output: output.write(original.read_bytes())
    comparison = get("/api/comparison/reports/"+report["comparison_receipt_id"])
    dataset = get("/api/simulation/runs/"+report["run_id"]+"/dataset")
    assert hashlib.sha256(report["comparison_canonical_json"].encode()).hexdigest() == report["comparison_receipt_id"]
    assert comparison["canonical_json"] == report["comparison_canonical_json"]
    assert digest(dataset) == report["dataset_sha256"] == comparison["report"]["candidate"]["provenance"]["source_sha256"]
    assert json.loads(report["dataset_canonical_json"]) == dataset
    assert report["input_revision"] == dataset["study_id"] and report["run_id"] == dataset["run_id"]
    native = get("/api/ngg/jobs/"+report["geometry_job_id"])
    assert native["state"] == "accepted" and native["byte_integrity"] and native["qa"]["qa-step"]["pass"]
    assert hashlib.sha256(report["geometry_qa_canonical_json"].encode()).hexdigest() == report["geometry_qa_sha256"]
    assert json.loads(report["geometry_qa_canonical_json"]) == native["qa"]
    for source in [*report["reproducibility"]["source_refs"], report["reproducibility"]["renderer_source"]]:
        assert filehash(ROOT/source["path"]) == source["sha256"]
    artifact = report["geometry_artifact"]
    assert artifact == native["record"]["artifacts"][0]
    out = HERE/"native-handoff"; out.mkdir()
    directory = STATE/"ngg_software_candidates"/report["geometry_job_id"]
    for name, expected in ((Path(artifact["storage_uri"]).name, artifact["sha256"]), ("source.brep", artifact["source_artifact_sha256"])):
        raw = checked_file(directory, name, expected).read_bytes()
        with (out/name).open("xb") as output: output.write(raw)
        assert filehash(out/name) == expected
    save("native-source.json", native); save("p09-dataset.json", dataset); save("p10-comparison.json", comparison)
    archive = (HERE/"review-package.zip").read_bytes()
    assert archive == (HERE/"downloaded-review-package.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        assert package.testzip() is None and set(package.namelist()) == {"report.json", "report.md", "report.html", "manifest.json"}
        manifest = json.loads(package.read("manifest.json"))
        assert manifest["report_id"] == key and manifest["production_handoff"] is False
        for name, expected in manifest["files"].items():
            assert hashlib.sha256(package.read(name)).hexdigest() == expected
            assert package.read(name) == (HERE/name).read_bytes()
        assert package.read("report.json") == receipt["canonical_json"].encode()
        assert b"Method and SI operating conditions" in package.read("report.md")
    assert report["status"]["experimental_validation"] == "not-performed" and report["status"]["production_handoff"] is False
    assert live["review_intents"] and all(v["independent_acceptance"] is False for v in live["review_intents"])
    save("signoff-report.json", {"decision": "SOFTWARE_RESEARCH_REPORT_ONLY", "review_intents": live["review_intents"], "signed_human_approval": False,
        "experimental_validation": "NOT_PERFORMED", "production_handoff": "BLOCKED", "independent_engineering_acceptance": "PENDING"})
    save("provenance-integrity.json", {"pass": True, "report_sha256": key, "study_id": report["input_revision"], "run_id": report["run_id"],
        "geometry_snapshot_id": report["geometry_snapshot_id"], "artifact_export_sha256": artifact["sha256"], "artifact_source_sha256": artifact["source_artifact_sha256"],
        "package_sha256": hashlib.sha256(archive).hexdigest(), "manifest_files_checked": 3, "exact_native_bytes_retained": True,
        "renderer_source_checked": True, "source_claim_contract": "Synthetic explicit source/review fixture, not an independent approved engineering source or experiment",
        "comparison_and_dataset_checksums_match": True, "independent_acceptance": False})
    save("collection-performance.json", {"elapsed_s": time.perf_counter()-tick, "cumulative_python_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "Local evidence collection process only; not native/Chrome/whole-app/large-corpus peak or release budget"})
    spec = importlib.util.spec_from_file_location("p05_parity", HERE.parent/"P05_2026-10-09/physics_parity.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    physics = module.run(); baseline = HERE.parent/"P10_2026-10-11/physics_after.json"
    assert physics == json.loads(baseline.read_text())
    save("physics_after.json", physics); save("physics_parity.json", {"pass": True, "cases": 5, "tolerance": 0, "baseline_sha256": filehash(baseline), "physical_validation": False})
    print(json.dumps({"provenance_integrity": "PASS", "package_files": 4, "actual_occt_to_report": "PASS", "physics_parity_cases": 5, "physical_validation": False}))


if __name__ == "__main__":
    main()
