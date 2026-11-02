# R07 broader component/editor/study-handoff implementation

Campaign began 2026-10-20; handoff 2026-10-21. Repository HEAD remains `293223ebef190eaa647e67dc581eb186b2b5d987` in the inherited dirty checkout. No commit, push, release, live-root migration or owner rollout was performed.

## Outcome

The declared bounded **R07 component/editor/geometry-study-preparation V1 software** is implemented and locally exercised end to end. It is no longer a divergent-nozzle-only workflow. Exact supported geometry, limits and exclusions are in `MODEL_CONTRACT.md`; launch/use instructions are in `OPERATOR_RUNBOOK.md`.

Implemented: chamber/convergent/throat/divergent wall or solid profiles; showerhead, impinging doublet/triplet, shear-coaxial and continuous-gap pintle geometry; actual internal axial-sector cooling passages with optional separate fluid domains; proper frame-tree placements; durable typed feature editing, dependency/output controls, invalid-input diagnostics and graph impact; immutable revisions, session undo/redo and explicit history restoration; per-part native/reimport/formula/topology/semantic QA; actual metrology and source-bound analytic axial sections; exact candidate exchanges/preview; independent reviewer controls, named selections/interfaces/material regions/mesh intent; accepted-analysis STEP and revision-bound **study setup**, not an engine solver.

The original fixture/PicoGK and divergent-nozzle paths are preserved and separately tested. No old Core, Physics or Numerics file changed. Nine existing orchestration/presentation/infrastructure files were intentionally extended; 1,392 preceding source files are unchanged, zero are unexpectedly changed/missing. Twenty-one new source files are recorded in `preservation.json`/`source-final.json`. New evidence utility scripts are separately linted.

## Architecture and implementation evidence

| Responsibility | Exact implementation paths |
|---|---|
| Typed bounded feature language, SI units, frame/DAG validation, independent geometry references | `systems/geometry/component_model.py`, `component_reference.py`, `component_sections.py` |
| Build policy, per-part QA and runtime composition | `systems/geometry/component_qa.py`, `component_workspace.py`; default-compatible audit hook in `systems/geometry/service.py`; extended Euler/forward-ceiling support in `systems/geometry/qa.py` |
| Native analytic construction, true Boolean cuts and proper placement | `plugins/geometry/component_protocol.py`, `component_adapter.py`, `workers/component_worker.py` |
| Independent metre STEP reimport, actual body/face witnesses and topology | `plugins/geometry/workers/component_step_reader.py` |
| Immutable source/revision/command authority and dependency freshness | `systems/geometry/component_authority.py`; existing R05 repositories/coordinator/supervisor; exact new namespace guard in `infrastructure/persistence/durable_jobs.py` |
| Independent review, exact entity/interface mapping and unaccepted remap proposals | `systems/geometry/component_review.py` |
| Component-specific study contracts, without weakening the sphere solver | `simulation/component_handoff.py` |
| Authenticated project routes and explicit runtime gate | `api/component_geometry.py`; default-preserving shared `api/nozzle_geometry.py`; composition/freshness in `api/project_authority.py`, `api/context_projects.py` |
| Project/editor and standalone Native Geometry experience | `gui/static/component-geometry.js`, `.css`, `workbench/native-geometry.html`; existing `projects.js`, `gui/server.py` composition |

Editor controls are serialized during asynchronous actions, with entered values protected while a command is in flight. Context switches reject dirty/uncertain drafts. Switching models resets session undo history; old immutable history remains available. A missing or changed native runtime disables new building/current selection rather than silently substituting fixture geometry or losing historical originals.

## Scientific/geometry issues found and fixed

1. OCCT wire construction replaces pre-wire edges: semantic face binding now uses actual constructed face edges and revolve/Boolean/transform history. Missing/ambiguous semantics block handoff; face enumeration is not a stable identity.
2. Repeated native face-history traversals made the full source-derived cooled wall exceed the execution budget. Native `TopTools_IndexedMapOfShape` identity maps cache exact history membership, preserving shape/labels rather than decimating source geometry. The final large workloads pass within the existing budgets.
3. A finite cutter's coincident end-cap zero could falsely label an open coolant-port interior as metal surface in the mathematical reference. Through-channel membership now uses the radial/angular constraints without an artificial retained port cap. A dedicated regression protects this case; all old and new native cases pass.
4. The real chamber stage exposes SI quantity outputs, not the similarly named internal scalar fields. Source seeding reads and validates the actual saved quantity contract.
5. Revision restoration/review/setup use existing repository snapshot purposes and schemas; no new database-purpose/migration semantics were invented. Raw review input is validated before constructing strict wire contracts.

These are software/reference corrections, not new combustion, injection, cooling-flow or structural physics. Signed CSG constraint residuals are labelled as such, not misrepresented as certified Euclidean/Hausdorff distances. Gmsh/OCP share OCCT; independent formulas/process/import are not independent kernels.

## Verification ledger

| Check | Observed result | Evidence |
|---|---|---|
| All seven supported component families + actual source-derived cooled engine in original/proper placed frames | **16 passed**, no skips | `native-components-v3.xml`, `.log` |
| Actual component health, launched-process cancellation, timeout and missing-process failure | **4 passed**, no skips, no accepted/partial CAD on failure | `native-recovery-v3.xml`, `.log` |
| Actual component HTTP editor/build/review/remap/setup, negative input/currentness/CAS/cancel/access and restart | **6 passed**, no skips | `component-http-v3.xml`, `.log` |
| Preserved selected nozzle native/HTTP qualification | **7 passed**, no skips | `native-nozzle-v3.xml`, `.log` |
| Preserved native reference fixtures | **31 passed**, no skips | `fixture-regression-v3.xml`, `.log` |
| Final JavaScript workflow/helpers | **430 passed**, zero failures/skips | `javascript-final.log` |
| Production Ruff + evidence utility Ruff | PASS | `ruff-final.log`, `evidence-tools-lint.log` |
| CI-scoped Mypy | **426 source files**, PASS | `mypy-final.log` |
| Existing seven strict TypeScript consumers | PASS, TypeScript 6.0.3, strict/no-emit | `typescript-final.log`, `typescript-install.log` and successful compiler exit |
| Explicit runtime boundary | Valid final profile accepted; **10 unsafe copies rejected**, no native execution | `runtime-negative-proof.json` |
| Final full Python suite and prior-case reconciliation | **3,580 passed / 122 explicit skips / zero failures or errors**; no preceding case removed | `full-python-verified.log`, `.xml`, `test-summary.json` |
| Preceding source preservation | **1,392 unchanged / 9 declared edits / 0 unexpected or missing**; old Core/Physics/Numerics unchanged | `preservation.json`, `source-final.json` |
| Actual browser → API → SQLite/native bytes → review/setup → restart | PASS using isolated synthetic accounts/project; no browser console errors | `ui-proof-before-restart.json`, `ui-proof-after-restart.json`, `ui-console.json`, screenshots |

The larger native workload retains all 81 divergent stations plus three upstream profile points, three channels and four distinct metal/fluid bodies. Contract/resource ceilings are not a promise of success at every combination of maxima. Larger/different intended-use profiles require explicit qualification; there is no hidden source resampling or engineering tolerance default. Wider optional native migration/study campaigns were not all rerun, and default-suite skips must not be counted as passes.

`runtime-qualified-v3.json` binds 164 runtime/source identities plus separate component and preserved-nozzle receipts. Original receipts were not rewritten. V1 is superseded by a worker import-format-only correction; V2 was prepared but never qualified. The final V3 campaign was rerun rather than copying an old test result onto changed sources. Supplementary component recovery tests exercise the same final identities.

## Actual browser result

Task root: `/private/tmp/cosmos-r07-components-qa.nYPwuc`; project `c0a41c41-8d3f-4d7a-8552-0b3bcbc3e24f`; full-profile model `fb27c313-da09-58fe-9911-501ec299571e`, current V4; build source `db4e9313-d9fa-5c4a-9471-5da25fc2cced`; durable job `8a422446-15a1-43f3-81f4-e0ed2a008d75`.

- Actual retained candidate: **123,984 triangles, 4 native solids, 1,182 native faces**; six retained stages. STEP/STL topology and dimensions pass; all semantic mappings pass.
- Independent reimport relative-volume errors are approximately `1.35e-13` to `2.69e-13`; sampled STEP reverse errors approximately `6.67e-15` to `1.03e-14 m`. These software fixture comparisons are not a physical accuracy guarantee.
- Independent review workflow: **34 named selections, 12 metal/coolant interface groups and 4 explicit material regions**. The actual distinct synthetic reviewer is plainly labelled NOT real sign-off; self-review is blocked. This exercises the workflow, not real intended-use acceptance.
- Study `cb8d8bdc-4d8f-5778-b40b-5528a67929fa` remains current after actual graceful server restart. It explicitly reports mesh `NOT_GENERATED`, execution `NOT_STARTED`, solver support false, physical validation `NOT_PERFORMED`.
- **Seven actual browser downloads**—source, STEP, STL, attempt, captured inputs, reviewed STEP and setup—match retained bytes before and after restart. Reviewed and original STEP are identical bytes; review changes authority/intent, not geometry.
- Browser editing/source seeding, native build/progress, body selection/orientation, actual coolant-domain preview, analytic axial section query, dirty-context guard, immutable save/undo/redo and final injector-editor smoke test were exercised. A second synthetic showerhead model also passed final-editor V1→V2→undo V3→redo V4 without changing the first model/review/study.

Screenshots: `ui-full-chamber.png`, `ui-coolant-domain.png`, `ui-injector-editor.png`, `ui-study-setup.png`, `ui-study-after-restart.png`. These are software QA observations, not the two genuine owner usability observations required elsewhere.

## Readiness and remaining gates

The requested broader R07 **bounded component/editor/study-preparation V1 software is COMPLETE_LOCALLY_QUALIFIED**. Final full-suite, native, recovery, source-preservation, static, browser/download and restart evidence is reconciled. This does not close manufacturing/hardware/physical acceptance, R08's broader intended-use interoperability qualification, R09 engine volume meshing/CFD/FEA, larger unqualified workloads, arbitrary mixed-backend conversion, helical/manifold/swirl extensions or real human engineering review. No experimental measurements have been supplied or fabricated.

The 122 full-suite skips include optional native campaigns and pre-existing Knowledge hashability gaps. The 20 component-native/recovery, six component HTTP, seven preserved nozzle and 31 fixture cases were explicitly executed separately, without skips. Their results are not inferred from the default-suite skip count. Other optional native campaigns were not all rerun.

All test writes are isolated task/test roots. The actual owner's live `cosmos_app_data` was not migrated or switched. The full-suite CEA cache fixture was protected/restored; expected SHA256 is `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`. This is local dirty-worktree evidence, **not remote CI, a release or production readiness**.

Closure: final full-suite reconciliation contains **59 new cases and zero preceding cases removed**. The verified task-owned listener on `127.0.0.1:8877` was gracefully stopped and the port rechecked free; task browser tabs 13 and 15 were closed. Synthetic QA state, evidence and downloaded originals were retained. No user service was stopped or changed. The isolated launch example uses port 8878, checked unused at handoff; choose another unused port if its state changes.
