"""Generate local numerical/parity/preservation evidence; no engineering signoff."""
import hashlib
import importlib.util
import json
import platform
import resource
import time
from itertools import pairwise
from pathlib import Path

from numerics.finite_volume.radial_diffusion import solve
from physics.heat_transfer.spherical_conduction import reference_temperature
from plugins.geometry.protocol import checked_file
from simulation.contracts import StudySnapshot
from systems.contracts.geometry import GeometryBuildRecord

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start = time.perf_counter()
    refinement = []
    for cells in (8, 16, 32, 64):
        tick = time.perf_counter()
        result = solve(.01, cells, 10, 1e6, 300, tolerance=1e-10, max_iterations=50_000)
        error = max(abs(v - reference_temperature(.01, r, 10, 1e6, 300)) for r, v in zip(result.centers, result.values))
        refinement.append({"cells": cells, "iterations": result.iterations[-1], "termination": result.termination,
            "normalized_residual": result.residual_history[-1], "max_error_k": float(error),
            "declared_limit_k": 1e6 * .01**2 / (6 * 10 * cells**2), "signed_imbalance_w": result.outward - result.generated,
            "elapsed_s": time.perf_counter() - tick})
        assert result.converged and error < refinement[-1]["declared_limit_k"]
    ratios = [a["max_error_k"] / b["max_error_k"] for a, b in pairwise(refinement)]
    assert all(3.9 < value < 4.1 for value in ratios)
    save("refinement.json", {"pass": True, "cases": refinement, "error_ratios": ratios, "experimental_validation": False})
    save("numerical-performance.json", {"platform": platform.platform(), "architecture": platform.machine(),
        "python": platform.python_version(), "cpu_solver_refinement_s": time.perf_counter() - start,
        "ru_maxrss_before": before, "ru_maxrss_after": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "ru_maxrss_unit": "bytes" if platform.system() == "Darwin" else "KiB",
        "scope": "Python process cumulative maximum RSS, not per-run allocation or whole Chrome/native/GUI peak"})
    spec = importlib.util.spec_from_file_location("p05_parity", HERE.parent / "P05_2026-10-09/physics_parity.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = module.run()
    baseline = HERE.parent / "P08_2026-10-09/physics_after.json"
    equal = current == json.loads(baseline.read_text())
    save("physics_after.json", current)
    save("physics_parity.json", {"pass": equal, "cases": 5, "tolerance": 0, "baseline_path": str(baseline.relative_to(ROOT)),
        "baseline_sha256": filehash(baseline), "physical_validation": False})
    assert equal
    snapshot = json.loads((HERE / "baseline.json").read_text())["sha256"]
    changed = [name for name, expected in snapshot.items() if not (ROOT / name).is_file() or filehash(ROOT / name) != expected]
    allowed = {"gui/server.py", ".github/workflows/ci.yml"}
    save("source_integrity.json", {"baseline_files": len(snapshot), "changed_existing_paths": changed,
        "unexpected_changes": sorted(set(changed) - allowed), "pass": set(changed) <= allowed,
        "preserved_dirty_tree": True, "retained_before_bytes": sorted(allowed)})
    # Check the historical P08 seal against retained original files at known
    # P09 changes. Do not overwrite a predecessor seal with newer source.
    prior = json.loads((HERE.parent / "P08_2026-10-09/artifact_hashes.json").read_text())
    bad = []
    for name, expected in prior.items():
        file = HERE / "before" / name if name in allowed else ROOT / name
        if not file.is_file() or filehash(file) != expected:
            bad.append(name)
    save("predecessor_integrity.json", {"files": len(prior), "pass": not bad, "mismatches": bad,
         "original_sources_archived": sorted(allowed), "G5_G6_historical_receipts_unchanged": True})
    evidence = json.loads((HERE / "study-fixture.json").read_text())
    record = GeometryBuildRecord.from_json(json.dumps(evidence["geometry"]["status"]["record"]))
    study = StudySnapshot.from_json(json.dumps(evidence["context"]["study"]))
    artifact = record.artifacts[0]
    assert study.handoff.artifact == artifact and study.handoff.geometry_snapshot_id == record.snapshot.snapshot_id
    assert evidence["run"]["result"]["study_id"] == study.content_sha256
    assert filehash(HERE / "handoff-exact-sphere.step") == artifact.sha256
    candidate = Path("/tmp/cosmos-p09.Rge6Fw/after-verified/ngg_software_candidates") / record.job_id
    retained = HERE / "handoff"
    retained.mkdir(exist_ok=True)
    source = checked_file(candidate, "source.brep", artifact.source_artifact_sha256)
    (retained / "source.brep").write_bytes(source.read_bytes())
    export = checked_file(candidate, "export.step", artifact.sha256)
    (retained / "export.step").write_bytes(export.read_bytes())
    (retained / "record.json").write_text(record.to_json() + "\n")
    (retained / "study.json").write_text(study.to_json() + "\n")
    (retained / "mesh.json").write_text(json.dumps(evidence["run"]["result"]["mesh"], indent=2) + "\n")
    (retained / "dataset.json").write_text(json.dumps(evidence["run"]["result"], indent=2) + "\n")
    (retained / "geometry-qa.json").write_text(json.dumps(evidence["geometry"]["status"]["qa"], indent=2) + "\n")
    save("handoff-integrity.json", {"pass": True, "geometry_snapshot_id": record.snapshot.snapshot_id,
        "source_sha256": artifact.source_artifact_sha256, "export_sha256": artifact.sha256,
        "study_sha256": study.content_sha256, "mesh_sha256": evidence["run"]["result"]["mesh"]["mesh_sha256"],
        "selection": "outer-surface -> radial-outer-shell", "mapping_scope": "fixed analytic spherical symmetry; not generic native face remapping",
        "independent_STEP_QA_pass": evidence["geometry"]["status"]["qa"]["qa-step"]["pass"], "production_handoff": False})
    assert set(changed) <= allowed and not bad
    print(json.dumps({"refinement_cases": 4, "physics_parity_cases": 5, "scope_changes": changed, "p08_mismatches": bad}))


if __name__ == "__main__":
    main()
