# P08 Native Geometry workbench implementation

**Software vertical slice: PASS. G6 local software evidence: PASS.**

Repository: `COSMOS-PVT-LTD/COSMOS-0.1`; starting HEAD `293223ebef190eaa647e67dc581eb186b2b5d987`; macOS arm64 local developer qualification, 2026-10-09. Dirty prior work preserved. No commits, pushes, GitHub CI, native packaged distribution or human UX/CAD owner acceptance were performed. Do not treat software gates as engineering approval.

## G5 prerequisite closed first

`../G5_CLOSURE_2026-10-09/G5_CLOSURE_REPORT.md` and `decision.json` close all three Boolean STEP fidelity failures and the sphere STL topology failure. All 54 original native checks plus two genuine wrong-radius refusals passed (56 total). Thirty retained records were independently re-audited; five convergence series preserved. Original P07 PARTIAL decision/failed exports are not rewritten. Its sealed code is archived under the closure's `before/` and old documentation/artifact hashes remain verified.

Fixes: correct native-mm import with explicit SI metric conversion, fixed-deflection trimmed bounds, proven spherical carrier/curvature classification with raw Unknown retained, trim-aware reverse projection, explicit STEP local/write unit conversion, tighter native-mm STL tessellation and versioned bounded exact-zero encoding. **No geometry QA tolerance was relaxed.** Full P08 current-source native regression and re-audit confirm the closure after the reusable fixture factory was moved into Systems.

## Delivered scope and architecture

This is the smallest real, independently testable slice over the existing qualified **software-fixture project**, not arbitrary rocket-engine geometry. Fixed 10mm sphere/Boolean references, two actual backends, three explicit PicoGK voxel sizes. No arbitrary radii, engine CAD, trusted engineering review/publication, simulation mesh handoff or hardware approval. Box/cylinder remain qualified backend fixtures but are not exposed as editable workbench models in this slice.

Frozen direction remains **GUI -> API -> Systems -> plugin/infrastructure**. GUI contains display/interaction only; scientific DTOs, lineage, QA, measurement and worker decisions stay server-side. A regression test initially found direct GUI contract imports; those were moved behind `api/ngg_workbench.py` and all architecture tests subsequently passed. Existing DesignStore and physics modules are neither replaced nor given a competing store. Session geometry context is ephemeral, explicit P06 immutable snapshots/graphs/requests, not another persisted engineering design authority.

| Requirement / symbol | Implementation and evidence |
| --- | --- |
| Opt-in route, catalog, rollback | `gui/server.py:CosmosApplication.ngg_workspace`, `CosmosApplicationHandler` hooks; `gui/ngg.py:enabled`; `gui/static/app-shell/shell.js` advertises Native Geometry only from enabled server catalog. `COSMOS_NGG` + existing modern-shell flag both default off. Flag-off catalog remains 12 workbenches; existing routes/legacy assets remain functional. |
| Typed SI context, feature/parameter inspector | `systems/geometry/software_fixtures.py:case`, `workbench.py:Revision`, `context/change/activate`; immutable P06 hashes, source references, frame/units, server revision identity. `tests/fixtures/ngg_cases.py` now re-exports the same factory; application never imports tests. Feature tree, dependencies, units and exact DTOs visible. |
| Model tree / right contextual inspector / shell layout | `gui/static/workbench/native-geometry.html`, `gui/static/ngg/styles.css`: tree, central viewport, contextual inspector in wide focus layout; stacked responsive layout. Reuses shell resizable docks and theme/font/project controls. New focus mode is session-only, automatically removes narrow-screen dock overlap without changing persisted preferences. |
| Undo/redo / reload | `workbench.py:change/activate`, `view.js`: activates existing immutable revisions, not client-authored numerical state. Browser reload discovers retained jobs; source/graph/job freshness enforced by server. Session/revision/job admission bounded. |
| Actual native build queue / cancellation | `workbench.py:build/status/cancel`, existing `GeometryBuildService`, adapters and `WorkerSupervisor`. One native worker/2 queued, coordinator admission 3/backend; no synthetic percentage. P06 actual events and independently accepted/rejected QA shown. |
| Viewport / section / measurement | `plugins/geometry/workers/preview_reader.py`: separate bounded display-only STEP triangulation. `viewport.js`: event-driven WebGL, fit, arrows/orbit, +/- and wheel zoom, orthographic views, visual X clip. PicoGK displays actual accepted STL; STEP viewport is a labelled coarse display mesh, never substituted for analytic export. `workbench.py:measure` computes SI sampled-vertex distance on server; bounds/volume/centroid state provenance and limits. No CAD section surface or analytic-feature metrology is claimed. |
| Verification and fidelity | Design-system `EngineeringStatus`, `ParameterTable`, `ProjectTree`, `JobMonitor`, `ErrorDetails`, `EvidenceLink`. Execution/freshness/verification/physical-validation axes remain distinct. Exact independent QA and request tolerance/representation/voxel/source hashes are visible. No invented engineering signoff. |
| Fixture exchange / independent reimport | `workbench.py:accepted/fixture_bytes/reimport`, `api/ngg_workbench.py:dispatch`, `view.js` wizard. Only current Accepted, hash-verified, actor-owned candidates may be downloaded as **software fixtures**. Immutable source/bytes/snapshot checks run again. Exact uploaded bytes reimported and independently QA-checked. `GeometryBuildService.export()` stays `NOT_PUBLISHED`; no Published event/artifact is created. |
| Security / roles / resource bounds | `api/ngg_workbench.py:runtime_config/transport_guard/read_payload`: explicit G5 receipt/runtime hashes, no native auto-install or client worker commands/paths; auth, exact loopback Host/Origin; Engineer/Admin mutations only; request/triangle/file/session/job limits; JSON duplicate/nonfinite refusal; body read timeout. Foreign/stale/tampered/arbitrary uploads denied. Trusted local developer process isolation is not a hostile-code sandbox. |
| Typed GUI contracts | `gui/static/ngg/model.js`, `model.d.ts`; `tests/ui/ngg/type_contracts.ts`: exact lineage, finite bounded buffer, fixed artifact URLs and nonpublication guards; strict TypeScript check. |

## Executed final validation

| Validation | Actual result / retained evidence |
| --- | --- |
| Full Python regression | **2,581 passed, 65 skipped**, 52.77s; `logs/pytest-final2.{log,xml}`. 58 optional native cases are executed separately below; two optional prerequisite checks and five existing skips are not claimed executed. |
| Actual native current-source corpus | **58 passed**, 136.33s; `logs/native-final2.{log,xml}`: 54 original checks, two wrong-radius refusals, two real P08 workbench lineage/tamper/reimport/limit tests. `native-regression2/fixtures/` retains all 30 actual candidate records and exact files. |
| Independent repeat of native decisions | `candidate-reaudit.json`, `logs/reaudit-final.log`: all 30 records reparsed, source/export hashes and independent STEP/STL decisions repeated, five convergence series. Expected negative candidates remain refused. |
| API/role/architecture contracts | **42 passed**, `logs/role-contracts.log`; real loopback authentication and VIEWER/REVIEWER/APPROVER mutation refusals before native startup. Pure DTO/transport negative tests are separate from native evidence. |
| All JavaScript tests | **98 passed**, `logs/js-final2.log`. |
| Actual browser E2E / viewport | **12 passed**, `browser-tests.json`, `logs/browser-final3.log`: real two-backend build-inspect-download-reimport exact snapshot; native rejection/cancellation; stale/undo/redo; corrupt upload; display outage/recovery; keyboard/theme; responsive viewport unobscured hit-test; flag-off legacy compatibility. Only outage transport is explicitly mocked; native E2E/QA is real. |
| Accessibility | `accessibility-{dark,high-contrast}.json`: **0 axe WCAG 2 A/AA and 2.1 A/AA violations** in the NGG workbench; keyboard and modal Escape/focus-return tested. Not universal assistive-technology certification. |
| Performance | `viewport-performance.json`, both `e2e-*.json`: actual Chrome CPU draw/load timing and bounded buffer sizes; 812-triangle coarse STEP display and 14,940-triangle accepted PicoGK display. Event-driven rendering has no perpetual animation loop. CPU timings are not GPU/FPS/aggregate-memory certification or large engineering-model performance. |
| Scientific parity | `physics_parity.json`, `physics_{before,after}.json`: **5 real HTTP scientific cases match exactly**, zero numerical tolerance; excludes only recorded identity/time metadata. Existing incomplete engineering-review verdict is preserved. |
| Static/packaging-source checks | Ruff PASS; Mypy **332 source files** PASS; strict TS contracts PASS; JS syntax, Python compile and `git diff --check` PASS. No .app/signing/distribution acceptance claimed. |
| Preservation | `source_integrity.json`: 2,291 baseline files checked, only 8 explicitly scoped existing paths changed, prior unrelated edits preserved; original 483-file P07 seal verifiable against archived source + unchanged docs. Known CEA test timestamp was preserved as generated evidence then restored to exact original SHA256. |

## Evidence traceability and inventory

- `before-projects.png`: captured before P08 production changes; Native Geometry was disabled and route returned 404.
- `after-{occt,picogk}.png`, `responsive-{1024,390}.png`: actual live-native views. Visual inspection found then corrected mobile shell overlap; final tests additionally verify unobscured canvas centre, not just document width.
- `e2e-{occt,picogk}.json`: exact UI context, immutable build record, QA, downloaded SHA, independent reimport result and viewport metrics.
- `exchanged-fixtures/{occt,picogk}/`: exact corresponding source B-rep/VDB, downloaded STEP/conditioned STL, record, snapshot and QA; hashes and reimport snapshot bind these bytes, not regenerated substitutes.
- `local-runtime.json`, `native-regression-config.json`: explicit isolated runtime/receipt/source hashes. No binaries/dependencies added to app requirements. Tools reuse the existing local PicoGK/OCP/Gmsh and Playwright/axe/TypeScript installations.
- `logs/` retains initial failed diagnostic runs and final executed results. Acceptance uses final results only. `artifact_hashes.json` seals repository/evidence files; `finalize_evidence.py --verify` rechecks integrity, not test execution.

## Readiness / remaining gates

**P09 may be planned against this local software slice; P09 was not started.** Formal UX/CAD owner review/acceptance is still pending. General engine feature generation, persistent engineering project integration, named engineering selections, trusted review/publication, simulation handoff and native commercial packaging/security/other-platform acceptance remain explicit later scope. Human acceptance cannot be fabricated by this implementer. Software qualification does not establish manufacturability, safety or physical validity.

Rollout/rollback and controls: `gui/static/ngg/README.md`. The normal application remains default-off. Temporary fixture servers are stopped after validation; no user app/service or engineering project data is replaced.
