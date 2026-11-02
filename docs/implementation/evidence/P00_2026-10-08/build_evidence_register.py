"""Generate traceable P00 matrix/register, and check evidence/source preservation.

Only audit-evidence outputs are written. No production imports or source edits.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def main() -> None:
    baseline = json.loads((OUT / "repository_baseline.json").read_text())
    hashes = json.loads((OUT / "source_hashes.json").read_text())
    with (OUT / "source_inventory.csv").open(newline="") as stream:
        inventory = {row["path"]: row for row in csv.DictReader(stream)}
    # workbench, feature, state, source, symbol, scientific qualification
    entries = [
        ("Foundation", "SI quantities and dimensions", "IMPLEMENTED", "core/quantity.py", "Quantity", "Immutable Quantity; unit and affine-temperature contracts; not every Knowledge model is immutable."),
        ("Foundation", "Canonical unit registry", "IMPLEMENTED", "core/unit.py", "UnitRegistry", "Reuse as computation-unit authority."),
        ("Foundation", "Canonical serialization", "IMPLEMENTED", "core/serialization.py", "canonical_json_dumps", "Available foundation for content hashes; not by itself immutable artifact publication."),
        ("Rocket Engine", "Create/edit design", "PARTIAL", "systems/projects/models.py", "PropulsionDesign", "Active aggregate, revisions and change log; no complete immutable old-revision snapshots."),
        ("Rocket Engine", "Design persistence", "PARTIAL", "systems/persistence/design_store.py", "DesignStore", "Atomic latest-file replacement; stale preloaded writer overwrite reproduced; no transaction CAS."),
        ("Rocket Engine", "Validated edits", "IMPLEMENTED", "api/propulsion_workflow.py", "save_design", "API base_revision guard checks supplied aggregate; must retain it and add storage CAS."),
        ("Rocket Engine", "DAG and capability status", "IMPLEMENTED", "systems/workflow/graph.py", "build_default_propulsion_graph", "17 stages; cycle NOT_IMPLEMENTED; other maturity listed in workflow_inventory.json."),
        ("Rocket Engine", "Dependency invalidation", "IMPLEMENTED", "systems/workflow/invalidation.py", "invalidate_from_stage", "Current saved workflow freshness is not physical validation."),
        ("Rocket Engine", "CEA typed physics contract", "IMPLEMENTED", "physics/thermochemistry/cea_interface.py", "run_thermochemistry", "Explicit model/request/result and reactant range checks."),
        ("Rocket Engine", "Native NASA CEA adapter", "IMPLEMENTED", "plugins/nasa_cea/engine.py", "NasaCeaEngine", "CEA 3.3.4; 3 legacy Fortran comparisons pass; software/reference agreement only."),
        ("Rocket Engine", "Stage orchestration", "IMPLEMENTED", "systems/workflow/orchestrator.py", "run_phase3_chain", "Preliminary synchronous thermochemistry/performance chain; no durable background jobs."),
        ("Rocket Engine", "Liquid injector sizing", "PARTIAL", "physics/injectors/orifice.py", "liquid_orifice", "Liquid Cd/pressure-drop hydraulics; no atomization or combustion stability qualification."),
        ("Rocket Engine", "Single-phase regenerative cooling", "PARTIAL", "physics/heat_transfer/regenerative.py", "regenerative_cooling", "Divergent nozzle; constant properties and correlation validity bounds; no boiling/CHT."),
        ("Rocket Engine", "Gaseous slot-film cooling", "PARTIAL", "physics/heat_transfer/film_cooling.py", "effectiveness", "Qualified gas-film correlation, not general liquid evaporative film."),
        ("Rocket Engine", "Analytic divergent contour", "PARTIAL", "physics/compressible_flow/bell_nozzle.py", "bell_contour", "Geometry stations/CSV; not general MOC, optimized Rao or accepted CAD solid."),
        ("Rocket Engine", "MOC contour generation", "NOT_IMPLEMENTED", "physics/compressible_flow/moc_nozzle.py", "generate_contour", "Raises insufficient-data error; supported invariants must not be called contour generation."),
        ("Rocket Engine", "Materials catalog", "PARTIAL", "physics/materials/catalog.py", "get_material", "Property windows; no certified allowables."),
        ("Rocket Engine", "Thin-wall structural checks", "PARTIAL", "systems/stages/structure.py", "run_structure_stage", "Preliminary checks, not standalone Structures FEA/life workbench."),
        ("Rocket Engine", "Cycle power closure", "NOT_IMPLEMENTED", "systems/workflow/graph.py", "build_default_propulsion_graph", "Explicit unsupported cycle stage; preliminary bypass does not close pump/turbine balance."),
        ("Foundation", "Typed scientific result dimensions", "PARTIAL", "systems/contracts/results.py", "CalculationResult", "Status/validity/verification/validation/provenance present; envelope dictionaries still mutable."),
        ("Numerics", "1D Poisson solve", "IMPLEMENTED", "numerics/pde/poisson.py", "solve", "Generic kernel, not operational Simulation workbench."),
        ("Numerics", "1D finite-volume solve", "IMPLEMENTED", "numerics/finite_volume/fv_solver.py", "solve", "Refinement/microbenchmark evidence for small qualified fixtures, not general CFD."),
        ("Numerics", "Finite-element solve", "IMPLEMENTED", "numerics/finite_element/fem_solver.py", "solve", "Generic qualified foundation, not arbitrary 3D engineering FEA."),
        ("Numerics", "Parametric curve sampling", "IMPLEMENTED", "numerics/mesh/parametric_curve.py", "quadratic_bezier", "Sampling helper, not CAD topology kernel."),
        ("Numerics", "13 deferred algorithm modules", "DEFERRED", "numerics/automatic_differentiation/hessians.py", "", "Explicit metadata-only modules; exact 13 paths in repository_baseline.json."),
        ("Knowledge", "Versioned local source/index store", "IMPLEMENTED", "knowledge/storage/local_store.py", "LocalKnowledgeStore", "Checksummed manifests and integrity; not a scientific run-history store."),
        ("Knowledge", "Durable original/derivative vault", "IMPLEMENTED", "knowledge/workspace/vault.py", "DurableArtifactVault", "Reusable provenance pattern; geometry ownership requires deliberate separate contract."),
        ("Knowledge", "Local ingestion job/checkpoint state", "PARTIAL", "knowledge/workspace/jobs.py", "JobStore", "No generic asynchronous scientific process runner/cancellation implied."),
        ("Knowledge", "Evidence-aware local RAG", "IMPLEMENTED", "knowledge/production/local_rag_pipeline.py", "ProductionLocalRAGPipeline", "Empty browser query did not fabricate evidence; no physical validation or solver execution."),
        ("Knowledge", "Upload validation", "PARTIAL", "knowledge/workspace/security.py", "validate_upload", "Filename/path/size checks; HTTP body is loaded before cap, requiring ingress bounds."),
        ("UI", "Workbench registry", "IMPLEMENTED", "gui/workbenches/registry.py", "WorkbenchDefinition", "2 active, 10 planned. Active Rocket capabilities remain scientifically partial."),
    ]
    planned = ["Turbopumps", "PID", "Structures", "Rocket Staging", "Manufacturing", "Simulation", "Visualization", "Documentation", "Code Comparison", "PLM"]
    entries += [(name, "Standalone engineering workbench", "PLANNED", "gui/workbenches/registry.py", "WorkbenchDefinition", "Registry tile/shared detail route only; existing related helpers are not this workbench.") for name in planned]
    entries += [
        ("NGG", "Production kernel/build/artifact/QA pipeline", "NOT_IMPLEMENTED", "gui/workbenches/registry.py", "WorkbenchDefinition", "NGG not registered; no production kernel, B-rep round-trip or accepted topology pipeline."),
        ("Comparison and V&V", "Operational comparison workspace", "NOT_IMPLEMENTED", "gui/workbenches/registry.py", "WorkbenchDefinition", "Code Comparison planned tile is not scientific independent V&V; test fixtures exist separately."),
    ]
    rows = []
    for workbench, feature, state, path, symbol, note in entries:
        source = inventory[path]
        match = re.search(rf"(?:^|; ){re.escape(symbol)}:(\d+-\d+)(?:;|$)", source["symbols"]) if symbol else None
        line_range = match.group(1) if match else f"1-{source['lines']}"
        absent = state in {"NOT_IMPLEMENTED", "PLANNED", "DEFERRED"}
        rows.append({"workbench": workbench, "feature": feature, "implementation_status": state,
                     "repo_sha": baseline["repo_sha"], "path": path, "symbol": symbol or "CAPABILITY_STATE metadata",
                     "line_range": line_range, "test_command": "python -m pytest -q",
                     "test_result": "Baseline passed; feature absent/deferred (not operationally tested)" if absent else "Full baseline: 2234 passed, 5 skipped; see named tests/JUnit for coverage scope",
                     "confidence": "HIGH", "notes": note + " Baseline includes fingerprinted dirty tree; CSV maturity is scoped, not certification."})
    fields = ["workbench", "feature", "implementation_status", "repo_sha", "path", "symbol",
              "line_range", "test_command", "test_result", "confidence", "notes"]
    with (OUT / "AS_BUILT_CAPABILITY_MATRIX.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    claims = [
        ("E01", ["GOV-001", "GOV-006"], "SHA plus dirty-source identity and architecture inventory are verified", "PASS", ["repository_baseline.json", "source_hashes.json", "source_inventory.csv", "import_edges.json", "P00_AUDIT_REPORT.md"], ["git rev-parse HEAD", "git ls-remote origin HEAD refs/heads/main", "collect_baseline.py"]),
        ("E02", ["GOV-001", "GOV-004"], "Configured Python and JS regression baseline passes with explicit skips", "PASS_WITH_KNOWN_SKIPS", ["pytest.xml", "pytest.log", "javascript-tests.log", "P00_BASELINE_TESTS.md"], ["python -m pytest -q --junitxml=<evidence>/pytest.xml", "node --test tests/js/*.test.cjs"]),
        ("E03", ["GOV-001"], "Configured lint/type and static dependency checks pass", "PASS_SCOPED", ["ruff.log", "mypy.log", "diagnostic_probes.json"], ["ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools", "mypy core physics numerics systems api"]),
        ("E04", ["GOV-004"], "Native CEA agrees with three rounded legacy Fortran reference cases; no physical validation claimed", "PASS_SCOPED", ["cea_reference.json", "cea_reference.log", "06-native-cea-success.dom.txt", "screenshots/06-native-cea-result.png"], ["python scripts/verify_cea_reference.py --source-dir <recorded local Fortran source>"]),
        ("E05", ["GOV-004"], "14 numerics refinement studies and 5 warm microbenchmarks provide fixture-scoped evidence", "PASS_RECOVERED_INVOCATION", ["numerics_benchmarks.json", "numerics_benchmarks.log", "numerics_benchmarks_module.log"], ["python tools/benchmark_numerics_foundation.py [FAILED import path]", "PYTHONPATH=. python -m tools.benchmark_numerics_foundation [PASS]"]),
        ("E06", ["GOV-003", "UX-005"], "Two stale preloaded API/store writers lose the first saved change; full published snapshots absent", "GAP_CONFIRMED", ["diagnostic_probes.json", "inspect_baseline.py", "P00_AUDIT_REPORT.md"], ["python <evidence>/inspect_baseline.py"]),
        ("E07", ["GOV-003"], "Current result envelope inputs are mutable; immutable publication boundary is required", "GAP_CONFIRMED", ["diagnostic_probes.json", "P00_AUDIT_REPORT.md"], ["python <evidence>/inspect_baseline.py"]),
        ("E08", ["GOV-009"], "2 active and 10 planned workbenches; NGG and operational Simulation/V&V absent", "AS_BUILT_VERIFIED", ["workbench_inventory.json", "workflow_inventory.json", "AS_BUILT_CAPABILITY_MATRIX.csv", "screenshots/08-simulation-planned.png"], ["Registry/catalog inspection", "Browser navigation to planned Simulation"]),
        ("E09", ["UX-001", "UX-002", "UX-003", "UX-004", "UX-006", "UX-007"], "12 fresh journey screenshots plus DOM/keyboard/minimum-viewport spot checks; UX gaps documented", "AUDIT_COMPLETE_NOT_ACCESSIBILITY_CERTIFIED", ["P00_UI_UX_AUDIT.md", "keyboard-observations.json", "minimum-viewport-observations.json"] + [str(p.relative_to(OUT)) for p in sorted((OUT / "screenshots").glob("*.png"))], ["Browser fixture journey at 1280x720 and 1100x700", "Ctrl+K, Shift+Tab, Tab, Escape"]),
        ("E10", ["GOV-009"], "No-source Knowledge query correctly reports insufficient evidence", "PASS_SCOPED", ["09-knowledge.dom.txt", "10-knowledge-search.dom.txt", "screenshots/10-knowledge-no-evidence.png"], ["Browser empty-workspace search and chat"]),
        ("E11", ["GOV-002", "GOV-007", "GOV-010"], "Security/request-bound/job-isolation gaps remain; no penetration test claimed", "RELEASE_GAPS_SOURCE_REVIEW", ["P00_AUDIT_REPORT.md", "source_inventory.csv"], ["Targeted authentication/server/credential-vault source review"]),
        ("E12", ["GOV-002"], "Existing macOS app is unsigned; supported-target release qualification absent", "RELEASE_BLOCKED", ["macos-signature.log", "P00_BASELINE_TESTS.md"], ["plutil -lint dist/COSMOS 0.1.app/Contents/Info.plist [PASS]", "codesign --verify --deep --strict dist/COSMOS 0.1.app [FAIL unsigned]"]),
        ("E13", ["GOV-005", "GOV-006", "GOV-008", "NGG-001", "NGG-002", "NGG-003", "NGG-004", "NGG-005", "NGG-006", "NGG-007"], "Future phases and approval/rollback/representation/QA gates are planned, not implemented", "PLAN_ONLY", ["P00_IMPLEMENTATION_PLAN.md", "P00_AUDIT_REPORT.md"], ["Complete specification package review and as-built gap mapping"]),
    ]
    environment = {k: baseline[k] for k in ("platform", "machine", "python", "python_executable")}
    evidence = {"schema_version": 1, "gate_id": "G0", "commit_sha": baseline["repo_sha"],
                "source_fingerprint_sha256": baseline["snapshot_fingerprint_sha256"],
                "source_scope": "HEAD plus fingerprinted existing dirty working tree, evidence excluded",
                "environment": environment, "date": "2026-10-08", "reviewer": "Codex automated audit; human acceptance not claimed",
                "decision": "PASS for bounded as-built audit only", "blockers": [],
                "release_blockers": ["Security/packaging/support-target qualification", "Immutable publication and transactional lineage", "Unimplemented geometry/simulation/V&V capabilities"],
                "claims": [{"claim_id": cid, "gate_id": "G0", "requirement_ids": reqs, "claim": claim,
                            "commit_sha": baseline["repo_sha"], "source_fingerprint_sha256": baseline["snapshot_fingerprint_sha256"],
                            "environment": environment, "commands": commands, "test_artifacts": artifacts,
                            "reviewer": "Codex automated audit", "decision": decision, "date": "2026-10-08",
                            "blockers": [], "confidence": "HIGH for stated limited scope"}
                           for cid, reqs, claim, decision, artifacts, commands in claims]}
    missing = sorted({p for c in evidence["claims"] for p in c["test_artifacts"] if not (OUT / p).is_file()})
    changed = [p for p, sha in hashes.items() if not (ROOT / p).is_file()
               or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != sha]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert not missing, f"Missing evidence: {missing}"
    assert not changed, f"Original source changed: {changed}"
    assert head == baseline["repo_sha"], "HEAD changed during audit"
    (OUT / "EVIDENCE_REGISTER.json").write_text(json.dumps(evidence, indent=2) + "\n")
    gate = {"gate_id": "G0", "phase": "P00_REPOSITORY_AUDIT", "decision": "PASS",
            "date": "2026-10-08", "commit_sha_before": head, "commit_sha_after": head,
            "source_fingerprint_sha256": baseline["snapshot_fingerprint_sha256"],
            "requirements_addressed": ["P00 outputs", "G0 proof", "as-built mapping of GOV/UX/NGG requirements, not implementation compliance"],
            "paths_changed": ["docs/implementation/evidence/P00_2026-10-08/"],
            "production_files_changed": [], "original_source_hashes_changed": changed,
            "evidence_missing": missing, "python_passed": 2234, "python_skipped": 5,
            "javascript_passed": 23, "capability_rows": len(rows),
            "dependencies_added": [], "licenses_changed": [], "hosted_ci_run": False,
            "numerical_regression": "No production changes; current-tree suite/refinement/native CEA checks pass within recorded scope",
            "reviewer": "Codex automated audit; human engineering signoff not claimed",
            "blockers": [], "release_ready": False,
            "next": "P01_EXPERIENCE_ARCHITECTURE",
            "next_scope": "Information architecture and prototypes only; G1 review before full production redesign",
            "risks": evidence["release_blockers"]}
    (OUT / "G0_DECISION.json").write_text(json.dumps(gate, indent=2) + "\n")
    print(json.dumps({"capability_rows": len(rows), "claims": len(claims), "screenshots": 12,
                      "original_files_changed": changed, "missing_evidence": missing, "g0": "PASS"}))


if __name__ == "__main__":
    main()
