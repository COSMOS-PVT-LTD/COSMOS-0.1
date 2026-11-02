"""Compare the original audited files with explicitly declared phase edits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PHASE_EDITS = {
    # Accepted ADR-R05-001: include new persistence IO in the existing Mypy gate.
    ".github/workflows/ci.yml",
    "api/authorization.py", "api/ngg_workbench.py", "gui/server.py", "gui/knowledge_proxy.py",
    "gui/static/maharshi.js", "gui/static/maharshi.css", "gui/static/workbench/knowledge.html",
    "gui/workbenches/registry.py", "knowledge/workspace/backup.py", "knowledge/workspace/session.py",
    "knowledge/workspace/server.py", "knowledge/foundation/document_pipeline.py",
    "knowledge/ingestion_adapters/html.py", "knowledge/ingestion_adapters/normalize.py",
    "infrastructure/release/security.py", "physics/compressible_flow/moc_nozzle.py",
    "systems/contracts/results.py", "systems/projects/models.py", "systems/stages/operating_point.py",
    "systems/stages/thermochemistry.py", "tests/unit_tests/physics/test_compressible_flow.py",
    "tests/unit_tests/gui/test_ngg.py",
    "gui/static/propulsion-suite.js", "gui/static/propulsion-suite.css",
    "gui/static/workbench/rocket-engine.html", "gui/static/rocket-workbench/view.js",
    "gui/static/rocket-workbench/styles.css",
    "gui/static/rocket-workbench/contracts.d.ts", "tests/js/rocket_workbench.test.cjs",
    "gui/static/app-shell/model.js", "gui/static/app-shell/model.d.ts",
    "gui/static/app-shell/adapter.js", "gui/static/app-shell/adapter.d.ts",
    "gui/static/app-shell/shell.js", "tests/js/app_shell.test.cjs",
    "tests/ui/app-shell/type_contracts.ts", "tests/ui/app-shell/shell.spec.cjs",
    # R02/R03 completion: native explicit downloads, additive graph UI,
    # shared compact/focus controls, guarded commands and domain queue.
    "api/knowledge_reports.py", "gui/native_window.py", "gui/static/app-shell/styles.css",
    "gui/static/design-system/components.js", "gui/static/design-system/components.d.ts",
    "gui/static/ngg/view.js", "gui/static/simulation/view.js", "gui/static/comparison/view.js",
    "gui/static/knowledge-reports/view.js", "gui/static/knowledge-reports/styles.css",
    "gui/static/workbench/knowledge-reports.html", "api/propulsion_workflow.py",
    # R05.2: deny managed legacy-store bypass and attach scoped API transport.
    "systems/persistence/design_store.py", "gui/static/cosmos-api.js",
    # R05.3: additive host-side exact event sink; native math/QA unchanged.
    "systems/geometry/service.py",
    # R05.4: structural captured-input type and optional host monitor sink only.
    "simulation/workbench.py",
}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    baseline_path = root / "docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/baseline.json"
    baseline = json.loads(baseline_path.read_text())
    changed, unexpected, missing = [], [], []
    unchanged = 0
    for name, expected in baseline["sha256"].items():
        path = root / name
        if not path.is_file():
            missing.append(name)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual == expected:
            unchanged += 1
        else:
            item = {"path": name, "before_sha256": expected, "after_sha256": actual}
            (changed if name in PHASE_EDITS else unexpected).append(item)
    report = {"baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        "original_files": len(baseline["sha256"]), "unchanged": unchanged,
        "declared_phase_changes": changed, "unexpected_changes": unexpected, "missing": missing,
        "historical_evidence_not_resealed": True, "pass": not unexpected and not missing}
    destination = args.output.resolve() if args.output else root / "docs/implementation/evidence/R01_2026-10-13/root-preservation.json"
    if not destination.is_relative_to(root / "docs/implementation/evidence"):
        raise ValueError("Preservation reports must stay in the repository evidence directory")
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Preservation: {unchanged} unchanged, {len(changed)} declared edits, {len(unexpected)} unexpected, {len(missing)} missing.")
    if unexpected or missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
