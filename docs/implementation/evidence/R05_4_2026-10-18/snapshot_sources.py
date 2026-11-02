"""Record this slice's current sources; not a release or historical reseal."""
from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FILES = (
    "infrastructure/persistence/files.py",
    "infrastructure/persistence/schema.py",
    "infrastructure/persistence/sqlite_projects.py",
    "infrastructure/persistence/durable_jobs.py",
    "infrastructure/persistence/inventory.py",
    "infrastructure/persistence/study_runtime.py",
    "systems/persistence/project_repository.py",
    "systems/persistence/job_repository.py",
    "systems/geometry/source_contract.py",
    "systems/geometry/retained_source.py",
    "systems/projects/study_authority.py",
    "simulation/workbench.py",
    "simulation/contracts.py",
    "physics/heat_transfer/spherical_conduction.py",
    "numerics/finite_volume/radial_diffusion.py",
    "api/study_projects.py",
    "api/project_authority.py",
    "api/geometry_projects.py",
    "gui/server.py",
    "gui/static/projects.js",
    "scripts/verify_completion_preservation.py",
    "tests/unit_tests/infrastructure/test_project_authority.py",
    "tests/unit_tests/infrastructure/test_study_lineage.py",
    "tests/integration_tests/gui/test_study_project_http.py",
    "tests/integration_tests/geometry/test_managed_study_retention.py",
    "tests/js/project_authority.test.cjs",
    "tests/ui/r05_4/preview.py",
)


def main() -> None:
    sources = {}
    for name in FILES:
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing/aliased candidate source: {name}")
        data = path.read_bytes()
        sources[name] = {"sha256": sha256(data).hexdigest(), "bytes": len(data)}
    result = {
        "scope": "R05.4 first study/run slice source snapshot only",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_work_preserved": True,
        "release_or_physical_acceptance": False,
        "historical_evidence_not_resealed": True,
        "sources": sources,
    }
    Path(__file__).with_name("source-final.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Recorded {len(sources)} scoped source identities; no release receipt issued.")


if __name__ == "__main__":
    main()
