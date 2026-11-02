"""Retain exact executed logs, exchanged fixture bytes and preservation receipts."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

from plugins.geometry.protocol import checked_file
from systems.contracts.geometry import GeometryBuildRecord

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
scratch = Path(sys.argv[1]).resolve()
state = Path(sys.argv[2]).resolve()
logs = HERE / "logs"
logs.mkdir(exist_ok=True)
for source in scratch.iterdir():
    if source.is_file() and source.suffix in {".log", ".xml", ".json"}:
        shutil.copyfile(source, logs / source.name)
for backend in ("occt", "picogk"):
    evidence = json.loads((HERE / f"e2e-{backend}.json").read_text())
    record = GeometryBuildRecord.from_json(json.dumps(evidence["status"]["record"]))
    assert not record.published_artifacts
    assert record.snapshot.snapshot_id == evidence["context"]["snapshot"]["content_sha256"] == evidence["reimport"]["result"]["snapshot_id"]
    candidate = state / "ngg_software_candidates" / record.job_id
    target = HERE / "exchanged-fixtures" / backend
    target.mkdir(parents=True, exist_ok=False)
    for artifact in record.artifacts:
        file = checked_file(candidate, Path(artifact.storage_uri).name, artifact.sha256)
        shutil.copyfile(file, target / file.name)
        source = checked_file(candidate, "source.brep" if backend == "occt" else "source.vdb", artifact.source_artifact_sha256)
        shutil.copyfile(source, target / source.name)
    (target / "record.json").write_text(record.to_json() + "\n")
    (target / "qa.json").write_text(json.dumps(evidence["status"]["qa"], indent=2) + "\n")
    (target / "snapshot.json").write_text(record.snapshot.to_json() + "\n")
    assert record.artifacts[0].sha256 == evidence["reimport"]["result"]["artifact_sha256"]
before = json.loads((HERE.parent / "G5_CLOSURE_2026-10-09/source_before.json").read_text())
allowed = {"plugins/geometry/protocol.py", "plugins/geometry/workers/occt_worker.py", "plugins/geometry/workers/step_reader.py",
           "systems/geometry/service.py", "systems/geometry/step_qa.py", "gui/server.py", "gui/static/app-shell/shell.js", "tests/fixtures/ngg_cases.py"}
changed = []
for name, expected in before.items():
    path = ROOT / name
    assert path.is_file(), name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        changed.append(name)
assert set(changed) <= allowed, changed
old = json.loads((HERE.parent / "P07_2026-10-09/artifact_hashes.json").read_text())
for name, expected in old.items():
    path = ROOT / name if name.startswith("docs/") else HERE.parent / "G5_CLOSURE_2026-10-09/before" / name
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
receipt = {"pass": True, "original_checkpoint_files": len(before), "modified_existing_paths": changed,
           "unrelated_edits_preserved": True, "original_p07_seal_archived_and_verified": True,
           "known_cea_timestamp_restored_exactly": hashlib.sha256((ROOT / "cache/cea/test_key.json").read_bytes()).hexdigest() == before["cache/cea/test_key.json"],
           "e2e_exact_downloaded_bytes_retained": True, "formal_human_acceptance": False}
(HERE / "source_integrity.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"preservation": "PASS", "original_files": len(before), "modified_existing_paths": len(changed), "e2e_retained": 2}))
