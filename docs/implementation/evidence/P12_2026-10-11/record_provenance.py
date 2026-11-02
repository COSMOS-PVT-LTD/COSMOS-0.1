"""Keep exact packaged scientific evidence; never infer physical acceptance."""
import hashlib
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from simulation.contracts import StudySnapshot
from systems.contracts.geometry._wire import digest, dumps
from validation.reporting import EngineeringReports


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as handle:
        handle.write(json.dumps(value, indent=2) + "\n")


def main():
    receipt = json.loads((HERE / "packaged-report.json").read_text())
    report = receipt["report"]
    raw = receipt["canonical_json"].encode()
    assert sha(raw) == receipt["report_id"] and json.loads(raw) == report
    dataset = json.loads(report["dataset_canonical_json"])
    comparison = json.loads(report["comparison_canonical_json"])
    qa = json.loads(report["geometry_qa_canonical_json"])
    assert digest(dataset) == report["dataset_sha256"] == comparison["candidate"]["provenance"]["source_sha256"]
    assert sha(report["comparison_canonical_json"].encode()) == report["comparison_receipt_id"]
    assert sha(report["geometry_qa_canonical_json"].encode()) == report["geometry_qa_sha256"]
    study = StudySnapshot.from_json(dumps(dataset["study"]))
    assert study.content_sha256 == dataset["study_id"] == report["input_revision"]
    assert study.handoff.integrity_sha256 == report["geometry_qa_sha256"]
    assert dataset["run_id"] == report["run_id"]
    assert study.handoff.geometry_snapshot_id == report["geometry_snapshot_id"]
    assert qa["qa-step"]["pass"] and qa["qa-step"]["topology_pass"] and qa["qa-step"]["dimensions_pass"]
    root = Path(re.findall(r"data root=([^\n]+)", (HERE / "packaged-modern.log").read_text())[-1])
    native = root / "ngg_software_candidates" / report["geometry_job_id"]
    output = HERE / "packaged-native-handoff"
    output.mkdir(exist_ok=True)
    artifact = report["geometry_artifact"]
    for name, expected in (("source.brep", artifact["source_artifact_sha256"]), ("export.step", artifact["sha256"])):
        assert sha((native / name).read_bytes()) == expected
        if (output / name).exists():
            assert sha((output / name).read_bytes()) == expected
        else:
            shutil.copyfile(native / name, output / name)
    for source in [*report["reproducibility"]["source_refs"], report["reproducibility"]["renderer_source"]]:
        assert sha((ROOT / source["path"]).read_bytes()) == source["sha256"], source["path"]
    assert report["claims"] == []
    assert report["status"]["experimental_validation"] == "not-performed"
    assert report["status"]["independent_acceptance"] is report["status"]["production_handoff"] is False
    archive = (HERE / "packaged-review-package.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        assert package.testzip() is None
        manifest = json.loads(package.read("manifest.json"))
        assert manifest["report_id"] == receipt["report_id"] and manifest["production_handoff"] is False
        assert set(manifest["files"]) == {"report.json", "report.md", "report.html"}
        for name, expected in manifest["files"].items():
            value = package.read(name)
            assert sha(value) == expected
            with (HERE / ("packaged-export-" + name)).open("xb") as handle:
                handle.write(value)
        assert package.read("report.json") == raw
    service = EngineeringReports()
    service.session(report["actor"]).reports[receipt["report_id"]] = raw
    assert service.package(report["actor"], receipt["report_id"]) == archive
    save("packaged-dataset.json", dataset)
    save("packaged-comparison.json", comparison)
    save("packaged-geometry-qa.json", qa)
    save("provenance-integrity.json", {"pass": True, "report_sha256": receipt["report_id"], "package_sha256": sha(archive),
                                       "dataset_sha256": report["dataset_sha256"], "native_source_export_sha_verified": True,
                                       "source_renderer_sha_verified": True, "offline_package_reproduction": True,
                                       "manifest_files": 3, "invented_sources": False, "physical_validation": False, "independent_acceptance": False,
                                       "scope": "Actual qualified OCCT sphere fixture and steady spherical conduction, not rocket/hot-fire qualification"})
    print("Packaged native-study-comparison-report provenance and offline ZIP reproduction PASS")


if __name__ == "__main__":
    main()
