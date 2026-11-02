# P09 Simulation Workbench — local software vertical slice

Date: 2026-10-10. Repository: COSMOS-PVT-LTD/COSMOS-0.1. Baseline HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987` plus preserved working-tree changes. Environment: macOS arm64, Python 3.11.4, installed Chrome, existing pinned NumPy/native/Playwright tooling. No new dependency installation, kernel upgrade, Git commit, push, merge, remote CI execution or engineering publication.

## Decision

**G7 software PASS for the smallest independently testable local benchmark slice.** Actual qualified OCCT sphere generation and independent STEP QA feed an immutable study, a geometry-bound radial volume mesh, a real numerical solve, convergence/conservation diagnostics and scientific plots. P10 may start against these versioned software datasets. This is not completion of a general engine CFD/FEA product, full 3D mesher/field viewer, trusted production handoff, engineering review or experimental validation.

P08 evidence was verified before modification: 2,921 sealed files, G5/G6 software PASS, human acceptance false. Its historical seal remains verifiable with the two pre-P09 source files retained under `before/`; original receipts and all native source/runtime hashes are unchanged. New evidence does not rewrite old gates. `source_integrity.json` checks 2,922 baseline files: only `gui/server.py` and `.github/workflows/ci.yml` changed; no unrelated edit was overwritten. The known test-created CEA cache timestamp was retained as diagnostic evidence and restored to the exact original 247 bytes/SHA256.

## Verified as-built baseline and reuse

Simulation was a planned registry entry in `gui/workbenches/registry.py`, served by `gui/static/workbench/detail.html`. There was no working `simulation/` package or geometry-to-study service. P08 already provided `systems/geometry/workbench.py:GeometryWorkbench.accepted`, P06 immutable `GeometryArtifact`, `NamedSelection`, geometry graph and snapshot contracts, independent STEP QA and actor-owned candidate jobs. Existing `numerics/finite_volume/diffusion.py:flux` supplies the actual exterior diffusion-flux check. Existing design-system components and modern shell provide shared controls, resizable docks, themes, keyboard support and bounded tables. No existing scientific function was replaced.

## Architecture and implementation inventory

All source paths below are repository-relative.

| Concern | Source | Implemented scope |
|---|---|---|
| Immutable study/handoff | `simulation/contracts.py` | Exact artifact revision, source/export and independent-QA hashes, SI world frame, exact fixture selection, settings, model/solver source hashes; strict lossless P06 wire machinery |
| Study/mesh/run authority | `simulation/workbench.py` | Actor-scoped ephemeral immutable revisions, bounded histories, two admitted jobs/one executor, actual asynchronous computation, cancellation, typed failures, result-byte checksum, source checks and computed stale state |
| Numerical kernel | `numerics/finite_volume/radial_diffusion.py` | Conservative spherical volume diffusion; explicit Gauss-Seidel equation-residual termination; real flux balance; bounded iteration/event history; cancellation refusal |
| Independent physical reference | `physics/heat_transfer/spherical_conduction.py` | Declared synthetic constant-k spherical conduction reference, independent of numerical solution; derivation and acceptance basis in `BENCHMARK.md` |
| Authenticated application transport | `api/simulation_workbench.py` | Exact request fields, 32KiB body bound, finite typed settings, same-origin IPv4 loopback, Engineer/Admin writes, actor ownership, explicit production-handoff refusal |
| GUI boundary / rollout | `gui/simulation_ui.py`, `gui/server.py` | Thin API bridge, strict default-off `COSMOS_NEW_SIM_UI`, additive route/catalog/assets, lazy workspace and shutdown hook; original flag-off page remains unchanged |
| GUI/task flow | `gui/static/workbench/simulation.html`, `gui/static/simulation/{model.js,model.d.ts,view.js,styles.css}` | Study, mesh/selections, settings, run/history, monitor and radial field profile; explicit save/discard/undo/redo; API-derived science, no solver equations in UI |
| Shared controls | `gui/static/design-system/components.js`, `gui/static/app-shell/` | Reused ProjectTree, ParameterTable, JobMonitor, EngineeringStatus, PlotPanel, Legend and ErrorDetails; shell resizing, themes, display scaling and keyboard navigation; not duplicated or modified |
| CI configuration | `.github/workflows/ci.yml` | New Simulation root included in blocking Ruff/Mypy commands; original quality-gate command prefix preserved; no claim that remote CI ran |

The frozen architecture already identifies Simulation → Physics/Numerics and API → Simulation. This adds the first scoped Simulation implementation, not a new storage owner or replacement architecture. Geometry remains under Systems; the API consumes its accepted immutable candidates. GUI consumes API, never native workers or numerical functions. Existing engineering DesignStore records are neither read as inputs nor changed. Native dependencies remain owned by their qualified process boundary.

## Scientific and handoff scope

The case is an accepted centered 10mm OCCT sphere with independent STEP reimport/dimensional/topology QA. Only `sphere / occt` qualifies. Boolean and PicoGK geometry do not receive inferred boundary semantics. Both source B-rep and exported STEP bytes are checked. The revision-bound `outer-surface` selects the explicitly derived `radial-outer-shell` in a **1D spherical-symmetry volume mesh**, not the P08 coarse display triangles or an arbitrary 3D mesh. Mesh metadata retains artifact/source/QA hashes, geometry revision/snapshot, SI frame, named selection, material region and explicit cell constraints. This exact fixture mapping does not establish generic native face-ID persistence or automatic remapping.

Default model: k=10 W/(m K), q=1e6 W/m³, exterior T=300 K, center symmetry, 16 radial cells, normalized residual tolerance 1e-8 and maximum 10,000 iterations. Users must save changes explicitly; presentation modes never change settings. The independent expression is `T=Ts+q(R²-r²)/(6k)`. The conservation reference is 4.188790204786391 W. `refinement.json` executes 8/16/32/64 cells at explicit 1e-10 residual tolerance: all converge, analytic error falls by approximately four per doubling, and actual flux conservation passes. Fixture-specific error/residual/conservation limits and their analytic basis are in `BENCHMARK.md`.

The UI never reduces status to one success Boolean. It separately shows execution, termination reason, numerical convergence, conservation, scoped positive-finite-temperature checks, analytic software solution verification, experimental validation and pending engineering review. A genuine one-iteration solve completes execution but reports nonconvergence, failed conservation, no accepted solution verification, and recovery instructions. Steady elliptic conduction has no CFL/time-step metric; the UI explicitly says not applicable. Field view is a 1D radial temperature profile, not a fabricated 3D map. All plots declare quantity/unit; residual definition and linear scale are explicit; the legend states range, K, clipping and color map.

The production-handoff API returns `ENGINEERING_ACCEPTANCE_REQUIRED`, including for Admin. Fixture QA is not a human engineering signoff. No publication/review authority was invented.

## Executed evidence

| Check | Result and evidence |
|---|---|
| Pre-change focused numerical/physics/NGG baseline | 340 passed; `baseline-tests.log` |
| Full Python regression | **2,637 passed, 72 skipped**, `python-final3.log`, `pytest-final3.xml`; 7 new explicit-runtime native tests skipped here and executed separately; prior 65 skips retained |
| Real native geometry→study tests | **7 passed, zero skipped**, `native-final2.log`, `native-final.xml`; actual OCCT sphere builds/independent QA, repeated deterministic fields, genuine nonconvergence/cancellation, stale geometry, source/dataset corruption, ownership and recovery. Memory failure is explicitly injected, not a measured native OOM claim |
| JavaScript regressions/plot adapters | **114 passed**, zero failures; `javascript-final.log`; units/legend/ranges, histories, source lineage and false-validation claims have negative tests |
| Real Chrome browser scenarios | **10 passed**, no retries/flakes; `browser-final2.log`, `browser-tests.json`; actual native build→mesh→run, nonconvergence, explicit save/undo/history, stale handoff, corruption/recovery, keyboard/themes, responsive views and flag-off compatibility. Only corrupt-display transport is deliberately injected |
| Accessibility | **0 automated axe WCAG 2 A/AA and 2.1 A/AA violations** in each dark/high-contrast workbench check; `accessibility-*.json`; not a universal screen-reader/user-study certification |
| Existing scientific parity | **5 real HTTP cases match exactly**, zero numerical tolerance; `physics_parity.json`, `physics_after.json`; prior P08 baseline retained; no engine science changed |
| Static quality | Ruff PASS (`ruff-final.log`); Mypy PASS, **338 source files** (`mypy-final.log`); strict TypeScript display contracts PASS (`type-contracts-final.log`); JS syntax and `git diff --check` PASS |
| Numerical performance | Four refinement cases approximately 0.35s aggregate on this Mac; `numerical-performance.json`; process cumulative max RSS ~35MB, explicitly not whole GUI/native/browser memory |
| Plot/navigation performance | `plot-performance.json`: actual Chrome load/plot timings at 1440/1024/390 widths, four bounded plots and no document horizontal overflow. Measured small-case CPU timings are not GPU/FPS/large-engine-model qualification or a general performance release budget |
| Source/evidence preservation | `source_integrity.json`, `predecessor_integrity.json`, `handoff-integrity.json`; baseline user edits preserved and old seals unchanged |

Initial diagnostic failures remain in `browser-initial.log`, `native-tests.log`, `python-final.log` and `type-contracts.log`. Corrections: prevent a newly submitted run from briefly displaying the preceding result; preserve exact settings-field schemas in tests; use separate authenticated sessions when switching preview servers; append Simulation to the compatible CI Mypy command; use the installed TypeScript Node16 module-resolution mode. Acceptance uses only the final successful logs, not initial failures. Cancellation is checked again under the dataset commit lock; source/export tampering makes original immutable results stale rather than relabeling them current.

## Visual evidence and rollout

`before-simulation.png` captures the actual planned screen before production changes. `after-study.png`, `after-monitor.png`, `after-nonconverged.png` and `responsive-*.png` capture actual live views. Visual inspection confirms units, independent-reference plots, explicit status dimensions and recovery details. Shared shell layout preferences remain separate from scientific snapshots. Run/history rows are bounded, and large parameter tables use the reused 20-row window. Automated scripted scenarios are not independent human usability acceptance.

`study-fixture.json` binds the actual GUI/API geometry record, exact snapshot, handoff, study and run. `handoff/` retains the exact corresponding native source, exported STEP, QA, immutable study, mesh and dataset. `handoff-exact-sphere.step` is the actual downloaded export; checksums match, not a regenerated stand-in. `artifact_hashes.json` seals the finished source/evidence; `finalize_evidence.py --verify` checks integrity without claiming a test rerun.

Launch/stop/rollback instructions are in `gui/static/simulation/README.md`. The new feature is default off; unsetting `COSMOS_NEW_SIM_UI` restores the planned legacy screen/catalog and removes APIs. Preview studies are ephemeral server-session data; restart clears them without engineering project migration. Temporary validation servers are stopped at handoff. No user-running service is stopped.

## Remaining boundaries / P10 readiness

P10 may consume the immutable software benchmark study/mesh/result IDs, normalized residual history, conservation checks, independent-reference errors and source hashes. General engine CAD and boundary-remapping qualification, arbitrary 3D meshing, CFD/FEA/coupled solvers, large-field rendering, durable engineering study storage, independent engineering acceptance/production handoff, experimental validation, supported-platform packaging/security and remote CI remain later work. P10 was not executed.
