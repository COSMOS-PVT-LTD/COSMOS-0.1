"""Reparse retained P06 records, hash bytes, independently repeat export QA."""
import hashlib
import json
import os
from pathlib import Path

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from systems.contracts.geometry import GeometryBuildRecord
from systems.geometry.qa import FixtureReference, audit_mesh, read_stl
from systems.geometry.step_qa import audit_step

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import numpy as np
    config = json.loads(Path(os.environ["P07_NATIVE_CONFIG"]).read_text())
    for name, sha in config["sha256"].items():
        assert digest(Path(name)) == sha, name
    command = config["step_reader"]
    reader = WorkerCommand(tuple(command["argv"]), tuple(command["environment"].items()))
    entries = []
    with WorkerSupervisor() as supervisor:
        for path in sorted((Path(config["evidence_directory"]) / "fixtures").glob("*/record.json")):
            record = GeometryBuildRecord.from_json(path.read_text())
            detail = json.loads(path.with_name("qa.json").read_text())
            assert not record.published_artifacts and not detail["physical_validation_claimed"] and not detail["publishing_performed"]
            for artifact in record.artifacts:
                assert artifact.sha256 == digest(path.parent / Path(artifact.storage_uri).name)
                assert artifact.source_artifact_sha256 == digest(path.parent / ("source.vdb" if record.request.backend_id == "picogk" else "source.brep"))
            for name in ("stl", "step"):
                old = detail.get("qa-" + name)
                if old is None:
                    continue
                reference = FixtureReference(detail["operation"])
                if name == "stl":
                    filename = "export-conditioned.stl" if detail["conditioning_profile"] != "raw" else "export.stl"
                    new = audit_mesh(path.parent / filename, reference, voxel_m=record.request.voxel_resolution_m, export_tolerance_m=record.request.export_tolerance_m)
                else:
                    new = audit_step(path.parent / "export.step", reference, reader=reader, supervisor=supervisor,
                                     job_id="reaudit-" + path.parent.name, tolerance_m=record.request.export_tolerance_m)
                    old = {key: val for key, val in old.items() if key != "reader_observed_rss_bytes"}
                    new = {key: val for key, val in new.items() if key != "reader_observed_rss_bytes"}
                assert new == old, path
            if "conditioning" in detail:
                receipt = detail["conditioning"]
                assert receipt["source_export_sha256"] == digest(path.parent / "export.stl")
                assert receipt["conditioned_export_sha256"] == digest(path.parent / "export-conditioned.stl")
                _, raw, _ = read_stl(path.parent / "export.stl", allow_bad_normals=True)
                _, conditioned, _ = read_stl(path.parent / "export-conditioned.stl")
                cross = np.cross(raw[:, 1] - raw[:, 0], raw[:, 2] - raw[:, 0])
                assert np.array_equal(raw[np.any(cross != 0, axis=1)], conditioned)
            entries.append({"fixture": path.parent.name, "record_state": record.state.value, "lineage_and_hashes": True,
                            "repeated_independent_export_qa": True, "qa_pass": all(detail[key]["pass"] for key in detail if key.startswith("qa-")),
                            "published": False, "physical_validation": False})
    convergence = {}
    directory = Path(config["evidence_directory"]) / "fixtures"
    for operation in ("sphere", "union", "difference", "intersection", "self_union"):
        rows = []
        for voxel in (.001, .0005, .00025):
            data = json.loads((directory / f"pico-{operation}-{voxel}" / "qa.json").read_text())["qa-stl"]
            rows.append({"h_m": voxel, "relative_volume_error": data["relative_volume_error"], "forward_max_m": data["forward_max_m"],
                         "reverse_max_m": data["reverse_max_m"], "qa_pass": data["pass"]})
        assert all(rows[i]["relative_volume_error"] > rows[i+1]["relative_volume_error"] for i in range(2))
        convergence[operation] = rows
    result = {"pass": True, "meaning": "Evidence integrity and repeated decisions; NOT all geometries qualified", "records": entries,
              "convergence": convergence, "full_G5_pass": False, "conditioning_vertex_changes": 0, "silent_refinement": False}
    (HERE / "candidate-reaudit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"evidenceIntegrity": True, "records": len(entries), "convergenceSeries": len(convergence), "fullG5Pass": False}))


if __name__ == "__main__":
    main()
